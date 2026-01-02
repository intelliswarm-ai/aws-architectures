# Intelligent Document Processing Platform

A cloud-native **ML Platform** built with AWS Lambda (Python 3.12), SageMaker, Bedrock, and AI Services that demonstrates AWS Machine Learning capabilities through an intelligent document processing pipeline.

## Architecture

```
                           Document Processing Pipeline
================================================================================

    +------------------+         +-----------------+         +----------------+
    |   S3 Bucket      |-------->|   Document      |-------->|   DynamoDB     |
    |   (Raw Docs)     | S3 Event|   Ingestion     |         |   (State)      |
    +------------------+         +-----------------+         +----------------+
                                        |
                                        v
                               +------------------+
                               |  Step Functions  |
                               |    Workflow      |
                               +--------+---------+
                                        |
           +----------------------------+----------------------------+
           |                            |                            |
           v                            v                            v
    +--------------+            +--------------+            +--------------+
    |   Textract   |            |  Transcribe  |            | Rekognition  |
    |  (PDF/Image) |            |   (Audio)    |            |   (Image)    |
    +--------------+            +--------------+            +--------------+
           |                            |                            |
           +----------------------------+----------------------------+
                                        |
                                        v
                               +-----------------+
                               |   Comprehend    |
                               |   (NLP/NER)     |
                               +-----------------+
                                        |
                                        v
                               +-----------------+
                               |   SageMaker     |
                               |   (Classify)    |
                               +-----------------+
                                        |
                                        v
                               +-----------------+
                               |    Bedrock      |
                               | (Summarize/Q&A) |
                               +-----------------+
                                        |
                                        v
                               +-----------------+
                               |      SNS        |
                               |  (Notify)       |
                               +-----------------+
```

## Features

### ML Services Demonstrated
- **Amazon SageMaker** - Custom model training, real-time endpoints, model registry
- **Amazon Bedrock** - Claude 3 for summarization and Q&A generation
- **Amazon Textract** - Text extraction from PDFs and images
- **Amazon Comprehend** - Entity recognition, sentiment analysis, language detection
- **Amazon Rekognition** - Image analysis and object detection
- **Amazon Transcribe** - Audio to text transcription

### Technical Highlights
- **Python 3.12** - Modern Python with type hints
- **AWS Lambda Powertools** - Tracing, logging, metrics, idempotency
- **Pydantic** - Data validation and settings management
- **Step Functions** - Workflow orchestration with parallel processing
- **Infrastructure as Code** - Modular Terraform configuration

## Project Structure

```
aws-ml/
├── src/                             # Python Lambda source code
│   ├── common/                      # Shared models, utils, config
│   │   ├── __init__.py
│   │   ├── models.py                # Pydantic models
│   │   ├── clients.py               # AWS client configuration
│   │   ├── exceptions.py            # Custom exceptions
│   │   └── utils.py                 # Utility functions
│   ├── handlers/                    # Lambda handlers
│   │   ├── __init__.py
│   │   ├── document_ingestion.py    # S3-triggered ingestion
│   │   ├── text_extraction.py       # Textract integration
│   │   ├── audio_transcription.py   # Transcribe integration
│   │   ├── content_analysis.py      # Comprehend + Rekognition
│   │   ├── sagemaker_inference.py   # SageMaker endpoint invocation
│   │   ├── bedrock_generation.py    # Bedrock summarization/Q&A
│   │   ├── workflow_orchestration.py# Step Functions handlers
│   │   ├── training_pipeline.py     # SageMaker training management
│   │   └── notification.py          # SNS notification handler
│   └── services/                    # Business logic services
│       ├── __init__.py
│       ├── textract_service.py
│       ├── comprehend_service.py
│       ├── rekognition_service.py
│       ├── transcribe_service.py
│       ├── sagemaker_service.py
│       ├── bedrock_service.py
│       └── notification_service.py
├── sagemaker/                       # SageMaker training code
│   ├── training/                    # Training scripts
│   │   ├── train.py
│   │   ├── inference.py
│   │   └── preprocessing.py
│   ├── notebooks/                   # Jupyter notebooks
│   └── requirements.txt
├── tests/                           # Unit and integration tests
│   ├── __init__.py
│   ├── unit/
│   └── integration/
├── terraform/                       # Infrastructure as Code
│   ├── main.tf                      # Root module
│   ├── variables.tf                 # Configuration variables
│   ├── outputs.tf                   # Output values
│   └── modules/                     # Reusable modules
│       ├── lambda/                  # Lambda functions
│       ├── s3/                      # ML data buckets
│       ├── dynamodb/                # Document state table
│       ├── sqs/                     # Message queues
│       ├── sns/                     # Notifications
│       ├── step-functions/          # Workflow orchestration
│       ├── sagemaker/               # Endpoints & training
│       ├── bedrock/                 # Model access
│       ├── ai-services/             # Textract, Comprehend, etc.
│       ├── api-gateway/             # REST API
│       ├── eventbridge/             # Scheduled triggers
│       └── cloudwatch/              # Monitoring & alarms
├── scripts/                         # Build and deploy scripts
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
├── pyproject.toml                   # Python project configuration
└── README.md
```

## Prerequisites

- **Python 3.12+**
- **pip** or **uv** for package management
- **Terraform 1.5+**
- **AWS CLI** configured with appropriate credentials
- **AWS Account** with permissions for Lambda, SageMaker, Bedrock, S3, DynamoDB, Step Functions, SNS, EventBridge, CloudWatch, and AI Services

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project
cd aws-ml

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Build Lambda packages
./scripts/build.sh
```

### 2. Configure Terraform

```bash
cd terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit variables as needed
vim terraform.tfvars
```

### 3. Deploy Infrastructure

```bash
# Deploy all infrastructure
./scripts/deploy.sh

# Or manually
terraform init
terraform plan
terraform apply
```

### 4. Deploy SageMaker Model (Optional)

```bash
# Train and deploy a model
./scripts/deploy-model.sh
```

### 5. Test the Pipeline

Upload a document to the S3 raw bucket:

```bash
aws s3 cp sample-document.pdf s3://your-raw-bucket/input/
```

## Configuration

Key variables in `terraform.tfvars`:

```hcl
aws_region                = "eu-central-2"  # EU Zurich
environment               = "dev"
project_name              = "ml-platform"

# SageMaker
sagemaker_endpoint_instance_type = "ml.m5.large"
sagemaker_endpoint_instance_count = 1

# Bedrock
bedrock_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

# Notifications
notification_email = "admin@example.com"
```

## Lambda Functions

| Function | Trigger | Description |
|----------|---------|-------------|
| `document-ingestion` | S3 Event | Ingests uploaded documents |
| `text-extraction` | Step Functions | Extracts text via Textract |
| `audio-transcription` | Step Functions | Transcribes audio via Transcribe |
| `content-analysis` | Step Functions | Analyzes content (Comprehend + Rekognition) |
| `sagemaker-inference` | Step Functions / API | Classifies documents |
| `bedrock-generation` | Step Functions / API | Generates summaries and Q&A |
| `workflow-orchestration` | Step Functions | Routes and aggregates results |
| `training-pipeline` | EventBridge | Manages SageMaker training |
| `notification` | SNS | Sends notifications |

## AWS Services Used

### ML Platform
- **Amazon SageMaker** - Training, endpoints, model registry
- **Amazon Bedrock** - Foundation models (Claude)

### AI Services
- **Amazon Textract** - Document text extraction
- **Amazon Comprehend** - NLP and entity recognition
- **Amazon Rekognition** - Image analysis
- **Amazon Transcribe** - Speech to text

### Infrastructure
- **AWS Lambda** - Serverless compute
- **Amazon S3** - Document and model storage
- **Amazon DynamoDB** - State management
- **AWS Step Functions** - Workflow orchestration
- **Amazon SQS** - Message queuing
- **Amazon SNS** - Notifications
- **Amazon API Gateway** - REST API
- **Amazon EventBridge** - Scheduled triggers
- **Amazon CloudWatch** - Monitoring & alarms
- **AWS X-Ray** - Distributed tracing

## Development

### Running Tests

```bash
# Run all tests
./scripts/test.sh

# Or using pytest directly
pytest tests/ -v
```

### Running Locally

```bash
# Use SAM CLI for local testing
sam local invoke DocumentIngestionFunction --event events/s3_event.json
```

### Training a New Model

```bash
# Trigger training pipeline
./scripts/trigger-training.sh
```

## Cleanup

To destroy all resources:

```bash
./scripts/deploy.sh --destroy
```

Or manually:

```bash
cd terraform
terraform destroy
```

## Cost Considerations

This demo uses serverless and managed services with pay-per-use pricing:
- Lambda: First 1M requests free, then $0.20/1M
- SageMaker: Endpoint instance hours (ml.m5.large ~$0.115/hr)
- Bedrock: Per-token pricing varies by model
- AI Services: Per-request pricing (see AWS pricing)
- S3/DynamoDB/SQS/SNS: Minimal for development

**Tip**: Use the `--destroy` flag when not actively developing to minimize costs.

## License

This project is for educational and demonstration purposes.
