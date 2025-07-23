# 🖙 Voice-Based DPR Assistant (Pipecat + AWS Bedrock + Lambda)

A conversational voice agent that guides users through the creation of a Daily Progress Report (DPR) using real-time voice interaction. The assistant extracts and validates field inputs based on a knowledge base in AWS Bedrock and submits the final DPR as JSON to an AWS Lambda function for backend processing.

 Addtional Workshops for voice ai agents by aws : https://catalog.workshops.aws/voice-ai-agents/en-US/module1
---

## 📌 Features

- 🎤 Voice-based interface using Pipecat + WebRTC
- 🧠 Knowledge-aware question flow via AWS Bedrock
- 🗞 DPR fields collected and structured as JSON
- ☁️ JSON submitted directly to AWS Lambda
- 🛡️ Field validation strictly based on knowledge base definitions

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/voice-dpr-assistant.git
cd voice-dpr-assistant
```

### 2. Install Python & AWS CLI

- [Python 3.12](https://www.python.org/downloads/release/python-3120/)
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)

Make sure you're authenticated with AWS:

```bash
aws configure
```

---

### 3. Install Python Dependencies

Set up your virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install required packages:

```bash
pip install "pipecat-ai[webrtc,silero,aws-nova-sonic]"==0.0.67
pip install pipecat-ai-small-webrtc-prebuilt fastapi uvicorn python-dotenv boto3
```

---

### 4. Environment Configuration

Create a `.env` file in your project root:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
```

---

### 5. Run the Agent

```bash
python run.py agent.py
```

Open your browser and visit: [http://localhost:7860](http://localhost:7860)

---

## 🧹 Dependencies

| Package                                    | Purpose                                |
| ------------------------------------------ | -------------------------------------- |
| `boto3`                                    | AWS SDK to call Bedrock & Lambda       |
| `pipecat-ai[webrtc,silero,aws-nova-sonic]` | Core voice bot with VAD + AWS LLM      |
| `pipecat-ai-small-webrtc-prebuilt`         | WebRTC frontend package for browser UI |
| `fastapi` + `uvicorn`                      | Web server and API support             |
| `python-dotenv`                            | Loads AWS credentials from `.env`      |
| `Python 3.12`                              | Required runtime                       |
| `AWS CLI`                                  | AWS credential management              |

---

## 🧪 Build & Test

Start the voice agent:

```bash
python run.py agent.py
```

Watch the console for logs:

- Bedrock context response
- Collected user inputs
- Lambda invocation result

---
