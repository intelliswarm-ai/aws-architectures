# AWS SQS - Online Banking Platform with EC2 Auto Scaling

A distributed system architecture for a commercial bank's next-generation online banking platform. The system leverages Amazon EC2 for compute resources with Auto Scaling based on Amazon SQS queue depth, ensuring high scalability and cost-effectiveness.

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│ API Gateway │────▶│   Lambda    │
│ Application │     │             │     │  Producer   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                    ┌──────────────────────────────────┐
                    │         Amazon SQS Queue         │
                    │  (Transaction Messages Buffer)   │
                    └──────────────────┬───────────────┘
                                       │
                    ┌──────────────────┴───────────────┐
                    │     CloudWatch Custom Metric     │
                    │    (BacklogPerInstance Alarm)    │
                    └──────────────────┬───────────────┘
                                       │
                    ┌──────────────────▼───────────────┐
                    │     EC2 Auto Scaling Group       │
                    │ ┌─────────┐ ┌─────────┐ ┌──────┐ │
                    │ │  EC2-1  │ │  EC2-2  │ │ EC2-n│ │
                    │ │Processor│ │Processor│ │ ...  │ │
                    │ └────┬────┘ └────┬────┘ └──┬───┘ │
                    └──────┼───────────┼─────────┼─────┘
                           │           │         │
                           ▼           ▼         ▼
                    ┌──────────────────────────────────┐
                    │         DynamoDB Tables          │
                    │   (Transactions, Idempotency)    │
                    └──────────────────────────────────┘
```

## Key Features

### SQS-Based Auto Scaling
- **Target Tracking Policy**: Scales based on `BacklogPerInstance` custom metric
- **Scale Out**: Adds instances when queue depth exceeds target (100 messages/instance)
- **Scale In**: Removes instances when queue is below 50% of target capacity
- **Capacity Limits**: Min 2, Max 10 instances for cost control

### Distributed Messaging
- **Standard Queue**: High throughput, at-least-once delivery
- **Dead Letter Queue**: Captures failed messages after 3 retries
- **Visibility Timeout**: 60 seconds for processing
- **Long Polling**: 20 seconds wait for efficient polling

### Transaction Processing
- **Multiple Transaction Types**: Transfer, Payment, Deposit, Withdrawal, Balance Check
- **Idempotency**: Duplicate detection using DynamoDB
- **Multi-threaded Workers**: 4 worker threads per EC2 instance
- **Gunicorn WSGI**: Production-ready application server

## Tech Stack

- **Python 3.12** with type hints
- **Pydantic** for data validation
- **Flask** for health check endpoints
- **Gunicorn** for production deployment
- **AWS Lambda Powertools** for observability
- **Terraform** for infrastructure as code

## Project Structure

```
aws-sqs/
├── src/
│   ├── common/           # Shared utilities
│   │   ├── clients.py    # AWS clients
│   │   ├── config.py     # Configuration
│   │   ├── exceptions.py # Custom exceptions
│   │   └── models.py     # Data models
│   ├── handlers/         # Lambda handlers
│   │   ├── api_handler.py     # API Gateway handler
│   │   ├── dlq_handler.py     # DLQ processor
│   │   └── metrics_handler.py # Custom metrics publisher
│   ├── services/         # Business logic
│   │   ├── idempotency_service.py
│   │   ├── queue_service.py
│   │   └── transaction_service.py
│   └── application/      # EC2 application
│       ├── worker.py     # Transaction worker
│       ├── app.py        # Flask app
│       └── gunicorn_config.py
├── terraform/
│   ├── modules/
│   │   ├── vpc/          # VPC with subnets
│   │   ├── sqs/          # SQS queue + DLQ
│   │   ├── ec2/          # ASG + ALB
│   │   ├── iam/          # Roles and policies
│   │   ├── cloudwatch/   # Dashboards and alarms
│   │   └── s3/           # Deployment bucket
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   ├── build.sh
│   ├── deploy.sh
│   └── test.sh
└── docs/
    └── BUSINESS_LOGIC.md
```

## Quick Start

### Prerequisites

- Python 3.12+
- AWS CLI configured
- Terraform 1.5+

### Build

```bash
cd aws-sqs
./scripts/build.sh
```

### Deploy

```bash
# Deploy to dev environment
./scripts/deploy.sh -e dev

# Deploy with auto-approve
./scripts/deploy.sh -e dev --auto-approve

# Plan only
./scripts/deploy.sh -e dev --plan
```

### Test

```bash
# Run all tests
./scripts/test.sh

# Run unit tests only
./scripts/test.sh --unit

# Run with coverage
./scripts/test.sh --coverage
```

### Destroy

```bash
./scripts/destroy.sh -e dev
```

## Configuration

### Terraform Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_name` | Project name prefix | `banking-sqs` |
| `environment` | Environment (dev/staging/prod) | `dev` |
| `aws_region` | AWS region | `eu-central-2` |
| `asg_min_size` | Minimum ASG instances | `2` |
| `asg_max_size` | Maximum ASG instances | `10` |
| `target_messages_per_instance` | Scaling target | `100` |
| `ec2_instance_type` | EC2 instance type | `t3.medium` |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `TRANSACTION_QUEUE_URL` | SQS queue URL |
| `TRANSACTIONS_TABLE_NAME` | DynamoDB table name |
| `IDEMPOTENCY_TABLE_NAME` | Idempotency table name |
| `LOG_LEVEL` | Logging level (INFO/DEBUG) |

## API Endpoints

### Create Transaction
```bash
POST /transactions
{
    "transaction_type": "TRANSFER",
    "source_account": "1234567890",
    "target_account": "0987654321",
    "amount": 100.00,
    "currency": "USD",
    "idempotency_key": "unique-key-123"
}
```

### Get Transaction
```bash
GET /transactions/{transaction_id}
```

### Health Check
```bash
GET /health
```

### Queue Metrics
```bash
GET /metrics
```

## Scaling Behavior

### Scale-Out Scenario
```
Queue Depth: 500 messages
Running Instances: 2
BacklogPerInstance: 250 (above target of 100)
Action: Scale out to 5 instances
```

### Scale-In Scenario
```
Queue Depth: 50 messages
Running Instances: 5
BacklogPerInstance: 10 (below 50% of target)
Action: Scale in to 2 instances (minimum)
```

## Monitoring

### CloudWatch Dashboard
- Real-time queue depth
- Instance count over time
- BacklogPerInstance metric
- Transaction processing rate

### Alarms
| Alarm | Threshold | Action |
|-------|-----------|--------|
| High Queue Depth | > 1000 messages | SNS notification |
| Old Messages | > 5 minutes | SNS notification |
| DLQ Messages | > 10 messages | SNS notification |
| ASG Below Minimum | < 2 instances | SNS notification |

## Cost Optimization

- **Auto Scaling**: Pay only for capacity needed
- **SQS**: Per-request pricing (~$0.40/1M requests)
- **Spot Instances**: Consider for 70% cost savings
- **VPC Endpoints**: Reduce NAT Gateway data transfer

## Security

- **Private Subnets**: EC2 instances in private subnets
- **VPC Endpoints**: Private access to SQS and DynamoDB
- **IAM Least Privilege**: Minimal permissions per component
- **IMDSv2**: Required for instance metadata
- **Encryption**: SQS SSE, DynamoDB encryption at rest

## License

For educational and demonstration purposes.
