# AWS Prototypes

A collection of AWS serverless architecture prototypes demonstrating best practices for cloud-native application development. Each project showcases different AWS services, patterns, and implementation approaches.

## Projects

| Project | Description | Language | Key AWS Services |
|---------|-------------|----------|------------------|
| [aws-lambda](./aws-lambda) | Task Automation System | Java 21 | Lambda, SQS, DynamoDB, Step Functions |
| [aws-ml](./aws-ml) | Intelligent Document Processing | Python 3.12 | SageMaker, Bedrock, Textract, Comprehend |

---

## aws-lambda

**Task Automation System** - A serverless task processing pipeline demonstrating core Lambda patterns.

### Architecture Highlights
- **EventBridge** scheduled task generation
- **SQS** queue processing with partial batch failure handling
- **Step Functions** workflow orchestration with retry/catch
- **DynamoDB** state persistence
- **SNS** notifications

### Tech Stack
- Java 21 with SnapStart for fast cold starts
- AWS SDK v2 with optimized HTTP client
- AWS Lambda Powertools (tracing, logging, idempotency)
- Terraform modular infrastructure

### Quick Start
```bash
cd aws-lambda
./scripts/build.sh
./scripts/deploy.sh
```

[View full documentation](./aws-lambda/README.md)

---

## aws-ml

**Intelligent Document Processing Platform** - A full ML pipeline demonstrating AWS AI/ML services.

### Architecture Highlights
- **Document Ingestion** via S3 triggers
- **Text Extraction** with Textract (PDFs, images)
- **Audio Transcription** with Transcribe
- **Content Analysis** with Comprehend (NLP) and Rekognition (vision)
- **Document Classification** with SageMaker custom models
- **Summarization & Q&A** with Bedrock (Claude)
- **Workflow Orchestration** with Step Functions

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation
- AWS Lambda Powertools
- XGBoost for document classification
- Claude 3 Sonnet for generative AI
- Terraform modular infrastructure

### Quick Start
```bash
cd aws-ml
./scripts/build.sh
./scripts/deploy.sh
```

[View full documentation](./aws-ml/README.md)

---

## Common Patterns

Both projects demonstrate:

### Infrastructure as Code
- **Modular Terraform** - Reusable modules for Lambda, SQS, DynamoDB, etc.
- **Environment-based configuration** - Dev, staging, production support
- **Output values** for cross-stack references

### Serverless Best Practices
- **Event-driven architecture** - Loose coupling via events and queues
- **Idempotency** - Safe retries with deduplication
- **Error handling** - DLQs, retry policies, alerting
- **Observability** - CloudWatch logs, metrics, X-Ray tracing

### Security
- **IAM least privilege** - Minimal permissions per function
- **Secrets management** - Environment variables via Terraform
- **VPC isolation** - Optional private subnet deployment

---

## Prerequisites

### Common Requirements
- **AWS CLI** configured with appropriate credentials
- **Terraform 1.5+**
- **AWS Account** with admin or sufficient permissions

### aws-lambda (Java)
- Java 21 (Amazon Corretto recommended)
- Maven 3.8+

### aws-ml (Python)
- Python 3.12+
- pip or uv for package management

---

## AWS Region

All projects default to **eu-central-2** (EU Zurich). Modify `terraform.tfvars` to change:

```hcl
aws_region = "eu-central-2"  # EU Zurich
```

---

## Cost Considerations

Both projects use serverless, pay-per-use services:

| Service | Free Tier | Pricing |
|---------|-----------|---------|
| Lambda | 1M requests/month | $0.20/1M requests |
| SQS | 1M requests/month | $0.40/1M requests |
| DynamoDB | 25GB storage | On-demand per request |
| Step Functions | 4,000 transitions/month | $25/1M transitions |
| S3 | 5GB storage | $0.023/GB/month |
| SageMaker | None | Instance hours |
| Bedrock | None | Per-token pricing |

**Tip**: Use `./scripts/deploy.sh --destroy` to tear down resources when not in use.

---

## Project Structure

```
aws-prototypes/
├── README.md                 # This file
├── aws-lambda/               # Java Task Automation System
│   ├── lambda/               # Maven multi-module project
│   ├── terraform/            # Infrastructure
│   ├── scripts/              # Build/deploy scripts
│   └── README.md
└── aws-ml/                   # Python ML Platform
    ├── src/                  # Python Lambda source
    ├── sagemaker/            # Training code
    ├── terraform/            # Infrastructure
    ├── scripts/              # Build/deploy scripts
    └── README.md
```

---

## License

These projects are for educational and demonstration purposes.
