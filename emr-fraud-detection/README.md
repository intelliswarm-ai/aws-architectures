# EMR Spark Fraud Detection Pipeline

An ML-based fraud detection system that processes millions of financial transactions using Amazon EMR with Apache Spark. This architecture demonstrates real-time ingestion, feature engineering at scale, model training with Spark MLlib, and batch/streaming fraud scoring.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EMR SPARK FRAUD DETECTION PIPELINE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. INGESTION                                                               │
│  ┌─────────┐    ┌────────────┐    ┌────────┐     ┌─────────────────┐        │
│  │ Client  │───▶│API Gateway│───▶│ Lambda │───▶│ Kinesis Streams │        │
│  │ Apps    │    └────────────┘    └────────┘     └─────────────────┘        │
│  └─────────┘                                            │                   │
│                                                         ▼                   │
│  2. DATA LAKE (S3)                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐                 │
│  │   RAW    │  │ FEATURES │  │  MODELS  │  │ PREDICTIONS  │                 │
│  │  /raw/   │  │/features/│  │ /models/ │  │/predictions/ │                 │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘                 │
│       │              ▲              ▲              │                        │
│       ▼              │              │              ▼                        │
│  3. EMR SPARK PROCESSING                                                    │
│  ┌─────────────────────────────────────────────────────────┐                │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │                │
│  │  │  FEATURE    │─▶│   MODEL     │─▶ │   BATCH     │    │                │
│  │  │ ENGINEERING │   │  TRAINING   │   │  SCORING    │    │                │
│  │  └─────────────┘   └─────────────┘   └─────────────┘    │                │
│  └─────────────────────────────────────────────────────────┘                │
│                              │                                              │
│                              ▼                                              │
│  4. ORCHESTRATION (Step Functions)                                          │
│  ┌────────┐─▶ ┌──────────┐─▶┌──────────┐─▶┌──────────┐─▶┌─────────┐       │
│  │Trigger │   │Feature   │   │Training  │   │Scoring   │  │Results  │       │
│  └────────┘   └──────────┘   └──────────┘   └──────────┘  └─────────┘       │
│                                                              │              │
│                                                              ▼              │
│  5. RESULTS & ALERTING                                                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐                                 │
│  │ DynamoDB │  │   SNS    │  │ CloudWatch │                                 │
│  │ (Alerts) │  │ (Notify) │  │(Dashboard) │                                 │
│  └──────────┘  └──────────┘  └────────────┘                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Real-time Transaction Ingestion**: API Gateway + Lambda + Kinesis for high-throughput transaction processing
- **Feature Engineering at Scale**: Spark jobs compute velocity, behavioral, and distance features
- **ML Model Training**: Spark MLlib Random Forest for fraud classification
- **Dual Scoring Modes**:
  - **Batch Scoring**: Daily batch processing via Step Functions orchestrated EMR
  - **Streaming Scoring**: Near real-time scoring with Spark Structured Streaming
- **Transient EMR Clusters**: Cost-optimized clusters created per pipeline run
- **Comprehensive Alerting**: SNS notifications for fraud detection
- **Infrastructure as Code**: Both Terraform and CloudFormation support

## AWS Services Used

| Service | Purpose |
|---------|---------|
| **EMR** | Spark cluster for feature engineering, ML training, batch scoring |
| **Kinesis Data Streams** | Real-time transaction ingestion |
| **S3** | Data lake (raw, features, models, predictions) |
| **Lambda** | Ingestion, stream processing, orchestration, alerts, queries |
| **Step Functions** | ML pipeline orchestration |
| **DynamoDB** | Fraud alerts and prediction results |
| **SNS** | Real-time fraud notifications |
| **API Gateway** | REST API for ingestion and queries |
| **CloudWatch** | Monitoring dashboards and alarms |
| **VPC** | Network isolation for EMR |

## Project Structure

```
emr-fraud-detection/
├── src/
│   ├── common/           # Shared models, config, exceptions
│   ├── handlers/         # Lambda function handlers
│   └── services/         # AWS service wrappers
├── spark/
│   ├── jobs/            # Spark job scripts
│   └── utils/           # Spark utilities
├── terraform/           # Terraform IaC
│   └── modules/         # 11 Terraform modules
├── cloudformation/      # CloudFormation IaC
│   └── nested/          # 11 nested stacks
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/             # Build and deployment scripts
└── docs/               # Documentation
```

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.11+
- Terraform 1.5+ (for Terraform deployment)
- Docker (optional, for local testing)

### Build

```bash
# Build Lambda and Spark packages
./scripts/build.sh --all --clean
```

### Deploy with Terraform

```bash
# Initialize and deploy
cd terraform
terraform init
terraform workspace new dev
terraform apply -var="environment=dev"
```

### Deploy with CloudFormation

```bash
# Deploy using CloudFormation
./cloudformation/deploy-cfn.sh \
    --templates-bucket my-templates-bucket \
    --environment dev \
    --alert-email alerts@example.com
```

### Run Tests

```bash
# Run all tests with coverage
./scripts/test.sh --all --coverage
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /transactions | Ingest a new transaction |
| GET | /predictions | Query fraud predictions |
| GET | /alerts | Query fraud alerts |
| PUT | /alerts/{id}/acknowledge | Acknowledge an alert |
| GET | /health | Health check |

### Example: Submit Transaction

```bash
curl -X POST https://api.example.com/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ACC123456789",
    "merchant_id": "MERCHANT001",
    "transaction_type": "PURCHASE",
    "channel": "ONLINE",
    "amount": "150.50",
    "currency": "USD",
    "timestamp": "2024-01-15T14:30:00Z",
    "location": {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "country": "US"
    }
  }'
```

## ML Pipeline Execution

The Step Functions state machine orchestrates the ML pipeline:

1. **ValidateInput**: Validate execution parameters
2. **CreateEMRCluster**: Spin up transient EMR cluster
3. **FeatureEngineering**: Compute ML features from raw transactions
4. **ModelTraining**: Train/update Random Forest model (optional)
5. **BatchScoring**: Score transactions and generate predictions
6. **ProcessResults**: Aggregate results and generate alerts
7. **TerminateCluster**: Clean up EMR resources
8. **Notify**: Send pipeline completion notifications

### Trigger Pipeline

```bash
# Start pipeline execution
aws stepfunctions start-execution \
    --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:fraud-detection-dev-pipeline \
    --input '{"execution_date": "2024-01-15", "execution_mode": "FULL"}'
```

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | dev |
| `FRAUD_THRESHOLD` | Score threshold for fraud classification | 0.7 |
| `SUSPICIOUS_THRESHOLD` | Score threshold for suspicious classification | 0.4 |
| `MODEL_VERSION` | ML model version to use | v1.0 |
| `EMR_RELEASE_LABEL` | EMR release version | emr-7.0.0 |

## Monitoring

Access the CloudWatch dashboard for real-time monitoring:
- Kinesis stream throughput and iterator age
- Lambda invocations and errors
- EMR cluster and step status
- DynamoDB read/write capacity
- Fraud detection rate metrics

## Documentation

- [Business Logic](docs/BUSINESS_LOGIC.md) - Detailed explanation of fraud detection logic
- [Cost Simulation](docs/COST_SIMULATION.md) - Cost breakdown and optimization strategies

## Cost Optimization

- **Transient EMR Clusters**: Clusters are created per pipeline run and terminated after
- **Spot Instances**: Task nodes use spot instances (configurable)
- **S3 Lifecycle Policies**: Automatic data tiering to Glacier
- **DynamoDB On-Demand**: Pay-per-request billing for variable workloads

## Security

- VPC isolation for EMR clusters
- S3 bucket encryption (AES-256)
- DynamoDB encryption at rest
- SNS topic encryption (KMS)
- IAM roles with least-privilege policies
- VPC endpoints for S3 and DynamoDB

## License

This project is provided as an example architecture. See LICENSE for details.
