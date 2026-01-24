# ML Canary Deployment

A production-ready solution for deploying ML models with canary releases, traffic splitting, and A/B testing on Amazon SageMaker. Designed for media streaming companies serving millions of daily active users with sub-100ms inference latency requirements.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────────────────┐
│   API Gateway   │───▶│  Lambda Handlers │───▶│     SageMaker Endpoint          │
│   (REST API)    │    │  (Inference,     │    │  ┌─────────────────────────────┐│
└─────────────────┘    │   Deployment,    │    │  │  Production Variant (90%)   ││
                       │   Monitoring)    │    │  │  - Current stable model     ││
                       └──────────────────┘    │  └─────────────────────────────┘│
                              │                │  ┌─────────────────────────────┐│
                              ▼                │  │  Canary Variant (10%)       ││
┌─────────────────┐    ┌─────────────────┐     │  │  - New model version        ││
│   CloudWatch    │◀───│    DynamoDB     │     │  └─────────────────────────────┘│
│   (Metrics &    │    │  (Deployments,  │     └─────────────────────────────────┘
│    Alarms)      │    │   Metrics,      │                    │
└─────────────────┘    │   Events)       │    ┌──────────────────────────────────────┐
        │              └─────────────────┘    │   UpdateEndpointWeightsAndCapacities │
        ▼                                     │   (Gradual traffic shifting)         │
┌─────────────────┐    ┌─────────────────┐    └──────────────────────────────────────┘
│      SNS        │───▶│  Alert Email    │
│   (Alerts)      │    │  Notifications  │
└─────────────────┘    └─────────────────┘
```

## Features

- **Production Variants**: Deploy multiple model versions to a single SageMaker endpoint
- **Traffic Splitting**: Gradually shift traffic using `UpdateEndpointWeightsAndCapacities` API
- **A/B Testing**: Compare model performance with built-in metrics
- **Auto-Rollback**: Automatic rollback when latency or error rate thresholds are exceeded
- **Auto-Scaling**: Scale instances based on invocations per instance
- **Real-time Monitoring**: CloudWatch metrics, alarms, and dashboards
- **Sub-100ms Latency**: Optimized for low-latency inference

## Project Structure

```
ml-canary-deployment/
├── src/                          # Lambda function source code
│   ├── common/                   # Shared utilities
│   │   ├── models.py             # Pydantic data models
│   │   ├── config.py             # Settings and configuration
│   │   ├── clients.py            # AWS client management
│   │   ├── exceptions.py         # Custom exceptions
│   │   └── utils.py              # Utility functions
│   ├── handlers/                 # Lambda event handlers
│   │   ├── api_handler.py        # Real-time inference API
│   │   ├── deployment_handler.py # Deployment management
│   │   ├── monitoring_handler.py # Metrics collection
│   │   ├── traffic_shift_handler.py # Traffic management
│   │   └── rollback_handler.py   # Rollback operations
│   └── services/                 # Business logic services
│       ├── inference_service.py  # SageMaker inference
│       ├── deployment_service.py # Deployment operations
│       ├── monitoring_service.py # CloudWatch metrics
│       ├── traffic_service.py    # Traffic management
│       └── notification_service.py # SNS notifications
├── sagemaker/                    # SageMaker training code
│   └── training/
│       ├── train.py              # XGBoost training script
│       ├── inference.py          # Model serving script
│       └── preprocessing.py      # Data preprocessing
├── terraform/                    # Terraform IaC
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
├── cloudformation/               # CloudFormation templates
│   ├── main.yaml
│   └── nested/
├── sam/                          # SAM for local development
│   ├── template.yaml
│   └── samconfig.toml
├── scripts/                      # Automation scripts
│   ├── build.sh
│   ├── deploy.sh
│   ├── destroy.sh
│   └── test.sh
├── tests/                        # Unit and integration tests
└── docs/                         # Documentation
    ├── BUSINESS_LOGIC.md
    └── COST_SIMULATION.md
```

## Prerequisites

- Python 3.12+
- AWS CLI configured with appropriate credentials
- Terraform 1.5+ (for Terraform deployment)
- AWS SAM CLI (for local development)
- Docker (for local testing)

## Quick Start

### 1. Clone and Setup

```bash
cd ml-canary-deployment
pip install -r requirements-dev.txt
```

### 2. Build Lambda Package

```bash
./scripts/build.sh
```

### 3. Deploy with Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 4. Create a Canary Deployment

```bash
# Create a new deployment with 10% traffic to canary
curl -X POST https://<api-endpoint>/deployments \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create",
    "config": {
      "endpoint_name": "ml-canary-deployment-dev-endpoint",
      "current_variant": {
        "variant_name": "production",
        "model_name": "current-model"
      },
      "canary_variant": {
        "variant_name": "canary",
        "model_name": "new-model-v2",
        "initial_weight": 0.1
      },
      "auto_rollback_enabled": true,
      "latency_threshold_ms": 100,
      "error_rate_threshold": 0.01
    }
  }'
```

### 5. Monitor Deployment

```bash
# Get deployment status
curl https://<api-endpoint>/deployments?deployment_id=<id>
```

### 6. Shift Traffic

```bash
# Increase canary traffic by 10%
curl -X POST https://<api-endpoint>/traffic \
  -H "Content-Type: application/json" \
  -d '{
    "action": "shift",
    "deployment_id": "<deployment-id>",
    "shift_amount": 0.1
  }'
```

### 7. Rollback (if needed)

```bash
curl -X POST https://<api-endpoint>/rollback \
  -H "Content-Type: application/json" \
  -d '{
    "action": "immediate",
    "deployment_id": "<deployment-id>",
    "reason": "Manual rollback due to increased latency"
  }'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | `eu-central-1` |
| `SAGEMAKER_ENDPOINT_NAME` | SageMaker endpoint name | - |
| `LATENCY_THRESHOLD_MS` | Max acceptable P99 latency | `100` |
| `ERROR_RATE_THRESHOLD` | Max acceptable error rate | `0.01` |
| `ENABLE_AUTO_ROLLBACK` | Auto rollback on threshold breach | `true` |
| `ENABLE_AUTO_SCALING` | Auto scaling for endpoint | `true` |

### Terraform Variables

See `terraform/variables.tf` for all available configuration options.

## AWS Services Used

- **Amazon SageMaker**: Model hosting with production variants
- **AWS Lambda**: Serverless compute for handlers
- **Amazon API Gateway**: REST API for inference and management
- **Amazon DynamoDB**: Deployment state and metrics storage
- **Amazon S3**: Model artifacts and logs
- **Amazon CloudWatch**: Monitoring, metrics, and alarms
- **Amazon SNS**: Alert notifications
- **Amazon EventBridge**: Scheduled monitoring

## Key Concepts

### Production Variants

SageMaker endpoints support multiple production variants, allowing you to:
- Deploy multiple model versions simultaneously
- Split traffic between variants using weights
- Update weights without endpoint downtime

### Traffic Shifting

Use `UpdateEndpointWeightsAndCapacities` API to:
- Gradually shift traffic from current to canary variant
- No endpoint downtime during traffic shifts
- Immediate rollback by setting canary weight to 0

### Auto-Rollback

The monitoring handler evaluates:
- P99 latency against threshold (default: 100ms)
- Error rate against threshold (default: 1%)
- Comparison with production variant metrics

If thresholds are exceeded, automatic rollback is triggered.

## Development

### Run Tests

```bash
./scripts/test.sh
```

### Local Development with SAM

```bash
cd sam
sam build
sam local invoke ApiHandler --event events/inference.json
```

### Linting and Type Checking

```bash
ruff check src tests
mypy src
```

## Cleanup

```bash
# Terraform
./scripts/destroy.sh

# CloudFormation
aws cloudformation delete-stack --stack-name ml-canary-deployment-dev
```

## Cost Considerations

See [COST_SIMULATION.md](docs/COST_SIMULATION.md) for detailed cost analysis.

Key cost drivers:
- SageMaker endpoint instances (primary cost)
- Lambda invocations
- API Gateway requests
- DynamoDB read/write operations
- CloudWatch metrics and logs

## References

- [SageMaker Production Variants](https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry-deploy.html)
- [UpdateEndpointWeightsAndCapacities API](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_UpdateEndpointWeightsAndCapacities.html)
- [SageMaker A/B Testing](https://docs.aws.amazon.com/sagemaker/latest/dg/model-ab-testing.html)

## License

This project is for educational and demonstration purposes.
