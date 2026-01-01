# AWS Examples

A collection of AWS architecture examples demonstrating best practices for cloud-native and hybrid application development. Each project showcases different AWS services, patterns, and implementation approaches including serverless, PaaS, and hybrid cloud architectures.

## Projects

| Project | Description | Language | Key AWS Services |
|---------|-------------|----------|------------------|
| [aws-lambda](./aws-lambda) | Task Automation System | Java 21 | Lambda, SQS, DynamoDB, Step Functions |
| [aws-ml](./aws-ml) | Intelligent Document Processing | Python 3.12 | SageMaker, Bedrock, Textract, Comprehend |
| [aws-serverless](./aws-serverless) | Multi-Tenant SaaS Platform (intelliswarm.ai) | Python 3.12 | Cognito, WAF, KMS, VPC, Bedrock, CloudTrail |
| [aws-kinesis](./aws-kinesis) | Real-Time GPS Tracking System | Python 3.12 | Kinesis Data Streams, Lambda, DynamoDB, S3 |
| [aws-elasticbeanstalk](./aws-elasticbeanstalk) | Hybrid Enterprise Inventory System | Java 21 | Elastic Beanstalk, VPN Gateway, S3, CloudWatch |

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

## aws-serverless

**Multi-Tenant SaaS Platform for intelliswarm.ai** - GenAI-powered email and CRM intelligence solution for enterprises of 50-10,000 employees.

### Use Case
- **Email Intelligence** - Connect Microsoft 365/Google Workspace mailboxes and analyze emails using GenAI (Amazon Bedrock/Claude)
- **CRM Integration** - Sync contacts, deals, and activities with Salesforce, HubSpot, or Dynamics 365
- **Smart Prioritization** - AI-powered email sentiment analysis, intent detection, and priority scoring
- **Action Extraction** - Automatically extract action items and tasks from email conversations

### Architecture Highlights
- **Cognito Authentication** with MFA, custom Lambda authorizer
- **VPC Integration** for private Lambda deployment with VPC Endpoints
- **WAF Protection** with rate limiting, SQL injection, and XSS prevention
- **KMS Encryption** for all data at rest
- **Secrets Manager** with automatic rotation for OAuth tokens
- **CloudTrail** multi-region audit logging with Insights
- **AWS Config** compliance monitoring with managed rules
- **Budgets** cost management with anomaly detection
- **Multi-Tenant** architecture with Cognito claims-based isolation

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation and settings
- JWT validation with python-jose
- AWS Lambda Powertools (logging, tracing, metrics)
- Amazon Bedrock (Claude 3 Sonnet) for GenAI
- Terraform modular infrastructure (20+ modules)

### Key Enterprise Features
- **IAM Permission Boundaries** - Prevent privilege escalation
- **VPC Endpoints** - Private AWS service access (S3, DynamoDB, Secrets Manager, Bedrock)
- **Multi-Environment** - Dev/staging/prod with security profiles
- **Cost Management** - Service-specific budgets with alerts

### Quick Start
```bash
cd aws-serverless
./scripts/build.sh
./scripts/deploy.sh --env dev
```

[View full documentation](./aws-serverless/README.md)

---

## aws-kinesis

**Real-Time GPS Tracking System** - A streaming data platform for delivery truck GPS tracking with multiple consumers.

### Use Case
A company tracking GPS coordinates from delivery trucks in real-time. Coordinates are transmitted every 5 seconds, processed by multiple consumers, and aggregated for reporting.

### Architecture Highlights
- **Kinesis Data Streams** for high-throughput, real-time data ingestion
- **Multiple Consumers** processing the same stream:
  - Dashboard Consumer - Updates DynamoDB with latest truck positions
  - Geofence Consumer - Detects boundary crossings, publishes SNS alerts
  - Archive Consumer - Stores historical data in S3 for analytics
- **EventBridge** scheduled GPS producer (simulator)
- **DynamoDB** for current positions and geofence definitions
- **S3** with lifecycle policies for historical data archival

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation
- AWS Lambda Powertools (logging, tracing, metrics)
- Haversine formula for distance/geofence calculations
- Terraform modular infrastructure (7 modules)

### Key Features
- **Partition Key Design** - truck_id ensures ordered processing per truck
- **Fan-Out Pattern** - Multiple Lambda consumers from single stream
- **Geofence Detection** - Circle/polygon boundary detection with enter/exit alerts
- **Data Aggregation** - Per-truck statistics (distance, speed, idle time)
- **S3 Lifecycle** - Automatic tiering to IA/Glacier for cost optimization

### Quick Start
```bash
cd aws-kinesis
./scripts/build.sh
./scripts/deploy.sh
```

[View full documentation](./aws-kinesis/README.md)

---

## aws-elasticbeanstalk

**Hybrid Enterprise Inventory System** - A migrated full-stack Java application running on AWS Elastic Beanstalk with hybrid connectivity to an on-premises Oracle database.

### Use Case
A company migrating their legacy on-premises inventory management system to AWS. Due to compliance requirements and existing Oracle investments, the database remains on-premises while the application layer moves to AWS, connected via VPN/Direct Connect.

### Architecture Highlights
- **Elastic Beanstalk** managed Java platform with auto-scaling
- **VPN Gateway** secure connectivity to on-premises Oracle database
- **Hybrid Architecture** application in AWS, database on-premises
- **JasperReports** enterprise PDF/Excel report generation
- **S3** report storage with lifecycle policies
- **CloudWatch** monitoring, dashboards, and alarms

### Tech Stack
- Java 21 with Spring Boot 3.2
- Hibernate 6.x with Oracle dialect
- JasperReports 6.21 for reporting
- Thymeleaf for server-side templating
- Spring Security for authentication
- Terraform modular infrastructure (5 modules)

### Key Features
- **On-Premises Oracle** - No database migration required
- **VPN/Direct Connect** - Secure hybrid connectivity
- **Role-Based Access** - Admin, Manager, Staff roles
- **Report Generation** - Inventory and low-stock PDF/Excel reports
- **Multi-Cloud Ready** - Documentation for Azure/GCP equivalents

### Quick Start
```bash
cd aws-elasticbeanstalk
./scripts/build.sh
./scripts/deploy.sh -e dev
```

[View full documentation](./aws-elasticbeanstalk/README.md)

---

## Common Patterns

All projects demonstrate:

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
- **Secrets management** - Secrets Manager / Parameter Store
- **Encryption at rest** - KMS customer managed keys
- **VPC isolation** - Optional private subnet deployment

---

## Prerequisites

### Common Requirements
- **AWS CLI** configured with appropriate credentials
- **Terraform 1.5+**
- **AWS Account** with admin or sufficient permissions

### aws-lambda / aws-elasticbeanstalk (Java)
- Java 21 (Amazon Corretto recommended)
- Maven 3.9+

### aws-ml / aws-serverless / aws-kinesis (Python)
- Python 3.12+
- pip or uv for package management

---

## AWS Region

All projects default to **eu-central-2** (EU Zurich). Modify `terraform.tfvars` or environment files:

```hcl
aws_region = "eu-central-2"  # EU Zurich
```

---

## Cost Considerations

Most projects use serverless, pay-per-use services. The aws-elasticbeanstalk project uses EC2-based pricing:

| Service | Free Tier | Pricing |
|---------|-----------|---------|
| Lambda | 1M requests/month | $0.20/1M requests |
| SQS | 1M requests/month | $0.40/1M requests |
| DynamoDB | 25GB storage | On-demand per request |
| Step Functions | 4,000 transitions/month | $25/1M transitions |
| S3 | 5GB storage | $0.023/GB/month |
| Cognito | 50K MAU | $0.0055/MAU after |
| NAT Gateway | None | $0.045/hour + data |
| KMS | None | $1/key/month |
| Elastic Beanstalk | None (EC2 costs) | ~$30/mo per t3.medium |
| VPN Gateway | None | $0.05/hour (~$36/mo) |

**Tip**: Use `./scripts/deploy.sh --destroy` to tear down resources when not in use.

---

## Project Structure

```
aws-examples/
├── README.md                 # This file
├── aws-lambda/               # Java Task Automation System
│   ├── lambda/               # Maven multi-module project
│   ├── terraform/            # Infrastructure
│   ├── scripts/              # Build/deploy scripts
│   └── README.md
├── aws-ml/                   # Python ML Platform
│   ├── src/                  # Python Lambda source
│   ├── sagemaker/            # Training code
│   ├── terraform/            # Infrastructure
│   ├── scripts/              # Build/deploy scripts
│   └── README.md
├── aws-serverless/           # Enterprise API Platform
│   ├── src/                  # Python Lambda source
│   ├── terraform/            # Infrastructure
│   ├── environments/         # Dev/staging/prod configs
│   ├── scripts/              # Build/deploy scripts
│   └── README.md
├── aws-kinesis/              # Real-Time GPS Tracking
│   ├── src/                  # Python Lambda source
│   ├── terraform/            # Infrastructure (7 modules)
│   ├── tests/                # Unit and integration tests
│   ├── scripts/              # Build/deploy scripts
│   └── README.md
└── aws-elasticbeanstalk/     # Hybrid Enterprise Inventory
    ├── application/          # Spring Boot application
    │   ├── src/              # Java source (ai.intelliswarm.inventory)
    │   ├── .ebextensions/    # EB configuration
    │   └── pom.xml           # Maven configuration
    ├── terraform/            # Infrastructure (5 modules)
    ├── scripts/              # Build/deploy scripts
    └── README.md
```

---

## License

These projects are for educational and demonstration purposes.
