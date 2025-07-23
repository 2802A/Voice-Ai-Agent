# agent.py
import argparse
import os
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.aws_nova_sonic import AWSNovaSonicLLMService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
from pipecat.transports.network.webrtc_connection import SmallWebRTCConnection

import boto3

load_dotenv(override=True)

#BEDROCK_KB_ID This is the bedrock knowledge base id

# Function to retrieve context from Bedrock Knowledge Base
def get_bedrock_knowledge_context(query: str) -> str:
    bedrock = boto3.client("bedrock-agent-runtime", region_name=os.getenv("AWS_REGION"))

    response = bedrock.retrieve_and_generate(
        input={"text": query},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": BEDROCK_KB_ID,
                "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
            }
        }
    )

    return response["output"]["text"] if "output" in response and "text" in response["output"] else ""


# Create tools schema
tools = ToolsSchema(standard_tools=[])

async def run_bot(webrtc_connection: SmallWebRTCConnection, _: argparse.Namespace):
    logger.info(f"Starting bot")

    # Initialize the SmallWebRTCTransport with the connection
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_in_sample_rate=16000,
            audio_out_enabled=True,
            camera_in_enabled=False,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.8)),
        ),
    )
    # Specify initial system instruction
    # Get DPR field definitions from KB
    dpr_field_context = get_bedrock_knowledge_context("List all fields and definitions to create a Daily Progress Report")

    # Compose main system instruction
    system_instruction = (
        "You are a helpful assistant that guides the user in creating a Daily Progress Report (DPR). "
        "You must begin by asking the user for the required DPR fields one by one in a conversational way. "
        "Always start the conversation proactively without waiting for a user question.\n\n"
        "The DPR consists of specific required and optional fields. For each field:\n"
        "1. Ask for the field value clearly.\n"
        "2. Use ONLY definitions, requirements, and value rules as provided by the Bedrock Knowledge Base.\n"
        "3. Do NOT guess or invent any information not present in the KB.\n"
        "4. Validate responses only against the KB.\n"
        "5. Skip any auto-generated fields such as IDs or timestamps.\n\n"
        "Once all required fields are collected, confirm completion and notify the user that the DPR has been created.\n\n"
        "Stay strictly within the scope of the knowledge base. If the knowledge base lacks a field definition, ask the user to clarify or skip.\n"
        "After the DPR is created, just print everything in JSON format.\n\n"
        f"{AWSNovaSonicLLMService.AWAIT_TRIGGER_ASSISTANT_RESPONSE_INSTRUCTION}"
    )

# Build initial context with system instruction and user intent
    context = OpenAILLMContext(
        messages=[
            {"role": "system", "content": f"Knowledge base field definitions:\n{dpr_field_context}"},
            {"role": "user", "content": "I want to create a DPR"},
        ],
        tools=tools,
    )

    # Create the AWS Nova Sonic LLM service
    llm = AWSNovaSonicLLMService(
        secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        region=os.getenv("AWS_REGION"),  # as of 2025-05-06, us-east-1 is the only supported region
        voice_id="tiffany",  # matthew, tiffany, amy
    )

    context_aggregator = llm.create_context_aggregator(context)

    # Build the pipeline
    pipeline = Pipeline(
        [
            transport.input(),
            context_aggregator.user(),
            llm,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    # Configure the pipeline task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )
    # Handle client connection event
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected")
        # Retrieve the user's first message (or use a default)
        print(type(context_aggregator.user().get_context_frame()))
        # Kick off the conversation
        await task.queue_frames([context_aggregator.user().get_context_frame()])
        # Trigger the first assistant response
        await llm.trigger_assistant_response()

    # Handle client disconnection events
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")

    @transport.event_handler("on_client_closed")
    async def on_client_closed(transport, client):
        logger.info(f"Client closed connection")
        await task.cancel()
    # Run the pipeline
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
    
if __name__ == "__main__":
    from run import main
    main()