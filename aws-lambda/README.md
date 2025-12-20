# Task Automation System

A cloud-native **Task Automation System** built with AWS Lambda (Java 21) and Terraform that showcases Lambda's strengths: event-driven architecture, auto-scaling, AWS service integration, and serverless orchestration.

## Architecture

```
+------------------+     +-------------+     +-------------+
|   EventBridge    |---->|   Task      |---->|    SQS      |
|   Scheduler      |     |  Generator  |     |   Queue     |
+------------------+     +-------------+     +------+------+
                                                    |
                         +-------------+            v
                         |  DynamoDB   |<----+-------------+
                         | (Task State)|     | Task Worker |
                         +------+------+     +-------------+
                                |                   |
+------------------+            v                   v
|  Step Functions  |     +-------------+     +-------------+
| (Workflow Orch.) |---->|  Workflow   |---->|     SNS     |
+------------------+     |   Lambdas   |     | (Notify)    |
                         +-------------+     +-------------+
```

## Features

### Lambda Patterns Demonstrated
- **Scheduled Execution** - EventBridge triggers periodic task generation
- **Queue Processing** - SQS with partial batch failure handling
- **Workflow Orchestration** - Step Functions with retry/catch states
- **Event Notifications** - SNS for success/failure alerts
- **State Persistence** - DynamoDB for task tracking

### Technical Highlights
- **Java 21 + SnapStart** - Fast cold starts for Java Lambdas
- **AWS SDK v2** - Modern Java SDK with optimized HTTP client
- **Powertools** - Tracing, logging, idempotency
- **Partial Batch Failure** - Only failed messages returned to queue
- **Infrastructure as Code** - Modular Terraform configuration

## Project Structure

```
aws-practice/
├── lambda/                          # Java Lambda source code
│   ├── pom.xml                      # Parent Maven POM
│   ├── common/                      # Shared models, utils, config
│   ├── task-generator/              # Scheduled task generator
│   ├── task-worker/                 # SQS queue processor
│   ├── workflow-lambdas/            # Step Functions handlers
│   └── notification/                # SNS notification handler
├── terraform/                       # Infrastructure as Code
│   ├── main.tf                      # Root module
│   ├── variables.tf                 # Configuration variables
│   ├── outputs.tf                   # Output values
│   └── modules/                     # Reusable modules
│       ├── lambda/                  # Lambda with SnapStart
│       ├── sqs/                     # Queue + DLQ
│       ├── dynamodb/                # Task state table
│       ├── step-functions/          # Workflow orchestration
│       ├── eventbridge/             # Scheduled triggers
│       ├── sns/                     # Notifications
│       └── cloudwatch/              # Monitoring & alarms
├── scripts/                         # Build and deploy scripts
└── README.md
```

## Prerequisites

- **Java 21** (Amazon Corretto recommended)
- **Maven 3.8+**
- **Terraform 1.5+**
- **AWS CLI** configured with appropriate credentials
- **AWS Account** with permissions for Lambda, SQS, DynamoDB, Step Functions, SNS, EventBridge, CloudWatch

## Quick Start

### 1. Clone and Build

```bash
# Navigate to project
cd aws-practice

# Build Lambda JARs
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

### 3. Deploy

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy
terraform apply
```

Or use the deploy script:

```bash
./scripts/deploy.sh
```

### 4. Verify Deployment

After deployment, check:
1. **CloudWatch Dashboard** - View metrics and logs
2. **Step Functions Console** - See workflow executions
3. **SQS Console** - Monitor queue depth
4. **DynamoDB Console** - View task records

## Configuration

Key variables in `terraform.tfvars`:

```hcl
aws_region               = "us-east-1"
environment              = "dev"
task_generation_schedule = "rate(5 minutes)"
notification_email       = "admin@example.com"
```

## Lambda Functions

| Function | Trigger | Description |
|----------|---------|-------------|
| `task-generator` | EventBridge (cron) | Generates tasks on schedule |
| `task-worker` | SQS Queue | Processes tasks with batch handling |
| `validate-task` | Step Functions | Validates task input |
| `process-task` | Step Functions | Core task processing |
| `finalize-task` | Step Functions | Cleanup and notification |
| `notification` | SNS | Sends notifications |

## AWS Services Used

- **AWS Lambda** - Serverless compute
- **Amazon SQS** - Message queuing with DLQ
- **Amazon DynamoDB** - NoSQL task state storage
- **AWS Step Functions** - Workflow orchestration
- **Amazon EventBridge** - Scheduled triggers
- **Amazon SNS** - Notifications
- **Amazon CloudWatch** - Monitoring & alarms
- **AWS X-Ray** - Distributed tracing

## Development

### Running Tests

```bash
./scripts/test.sh
```

### Building a Single Module

```bash
cd lambda/task-generator
mvn clean package
```

### Local Development

Consider using:
- **LocalStack** for local AWS service emulation
- **SAM CLI** for local Lambda invocation
- **IntelliJ IDEA** with AWS Toolkit

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

This demo uses serverless services with pay-per-use pricing:
- Lambda: First 1M requests free, then $0.20/1M
- SQS: First 1M requests free
- DynamoDB: On-demand pricing
- Step Functions: $25/1M state transitions
- SNS: First 1M requests free

For development, costs should be minimal.

## License

This project is for educational and demonstration purposes.
