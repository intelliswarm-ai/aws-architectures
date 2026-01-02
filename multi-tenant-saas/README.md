# Enterprise Serverless Platform

A cloud-native **Multi-Tenant SaaS Platform** built with AWS Lambda (Python 3.12) for **intelliswarm.ai** - a GenAI-powered email and CRM intelligence solution for enterprises of 50-10,000 employees.

## Use Case

This platform enables enterprises to:
- **Email Intelligence** - Connect Microsoft 365/Google Workspace mailboxes and analyze emails using GenAI (Amazon Bedrock/Claude)
- **CRM Integration** - Sync contacts, deals, and activities with Salesforce, HubSpot, or Dynamics 365
- **Smart Prioritization** - AI-powered email sentiment analysis, intent detection, and priority scoring
- **Action Extraction** - Automatically extract action items and tasks from email conversations
- **Cross-Platform Sync** - Create CRM activities from analyzed emails automatically

## Architecture

```
                        Enterprise Serverless Architecture
================================================================================

    Internet
        |
        v
+------------------+     +------------------+     +------------------+
|       WAF        |---->|   API Gateway    |---->|     Cognito      |
| (Rate Limiting,  |     | (REST API with   |     | (User Pool +     |
|  SQL/XSS Rules)  |     |  Usage Plans)    |     |  Identity Pool)  |
+------------------+     +--------+---------+     +------------------+
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
           +---------------+           +---------------+
           |   Lambda      |           |   Lambda      |
           |  Authorizer   |           |   Handler     |
           | (JWT Verify)  |           | (Multi-Tenant)|
           +---------------+           +-------+-------+
                                              |
              +---------------+---------------+---------------+
              |               |               |               |
              v               v               v               v
    +------------------+ +----------+ +---------------+ +-----------+
    | Secrets Manager  | |   KMS    | |   DynamoDB    | |    SQS    |
    | (Rotation)       | |(Encrypt) | | (Per-Tenant)  | | (Async)   |
    +------------------+ +----------+ +---------------+ +-----------+
              |                               |               |
              v                               v               v
    +------------------+               +---------------+ +-----------+
    |   RDS/Aurora     |               |  EventBridge  | |    SNS    |
    | (Private Subnet) |               | (Cross-Acct)  | | (Notify)  |
    +------------------+               +---------------+ +-----------+

    All resources in VPC with VPC Endpoints for AWS Services
    CloudTrail + AWS Config for Compliance
    CloudWatch for Monitoring + Budgets for Cost Control
```

## Features

### Security & IAM
- **Cognito Authentication** - User pools with MFA, federated identity
- **Custom Lambda Authorizer** - JWT validation, fine-grained access control
- **Permission Boundaries** - Prevent privilege escalation
- **Cross-Account Access** - Secure AssumeRole with external ID
- **Secrets Rotation** - Automatic credential rotation via Lambda
- **KMS Encryption** - Customer-managed keys for all data at rest

### Network Security
- **VPC Integration** - Lambdas in private subnets
- **VPC Endpoints** - No internet access required for AWS services
- **Security Groups** - Fine-grained network ACLs
- **NAT Gateway** - Controlled outbound access (prod only)

### API Security
- **WAF Protection** - SQL injection, XSS, rate limiting
- **API Keys & Usage Plans** - Throttling and quotas per client
- **Request Validation** - Schema validation at API Gateway
- **Access Logging** - Full request/response audit

### Compliance & Audit
- **CloudTrail** - Multi-region API audit logging
- **AWS Config** - Compliance rules and remediation
- **GuardDuty** - Threat detection (prod)
- **Security Event Processing** - Real-time alerting

### Enterprise Patterns
- **Multi-Tenant Architecture** - Tenant isolation via Cognito claims
- **Multi-Environment** - Dev/staging/prod with different security profiles
- **Cost Management** - Budgets, alerts, tag-based allocation
- **Cross-Account EventBridge** - Enterprise event bus patterns

## Project Structure

```
aws-serverless/
├── src/                              # Python 3.12 Lambda source
│   ├── common/                       # Shared utilities
│   │   ├── config.py                 # Pydantic settings + Secrets Manager
│   │   ├── clients.py                # VPC-aware AWS clients
│   │   ├── models.py                 # Pydantic models
│   │   ├── security.py               # JWT validation, auth utilities
│   │   └── exceptions.py             # Custom exceptions
│   ├── handlers/                     # Lambda handlers
│   │   ├── api_handler.py            # API Gateway handler
│   │   ├── authorizer.py             # Custom Lambda authorizer
│   │   ├── async_processor.py        # SQS batch processor
│   │   ├── event_router.py           # EventBridge handler
│   │   ├── secret_rotation.py        # Secrets Manager rotation
│   │   ├── audit_handler.py          # CloudTrail processor
│   │   └── scheduled_task.py         # Scheduled jobs
│   └── services/                     # Business logic
│       ├── tenant_service.py         # Multi-tenant logic
│       ├── audit_service.py          # Audit logging
│       ├── email_service.py          # Email processing + GenAI
│       └── crm_service.py            # CRM integration + sync
├── terraform/                        # Infrastructure as Code
│   ├── main.tf                       # Root orchestration
│   ├── variables.tf                  # Configuration
│   ├── outputs.tf                    # Output values
│   ├── backend.tf                    # Remote state
│   └── modules/
│       ├── vpc/                      # VPC with private subnets
│       ├── security-groups/          # Network ACLs
│       ├── vpc-endpoints/            # AWS service endpoints
│       ├── lambda/                   # VPC-enabled Lambda
│       ├── api-gateway/              # REST API + WAF
│       ├── cognito/                  # User authentication
│       ├── secrets-manager/          # Secrets with rotation
│       ├── kms/                      # Encryption keys
│       ├── iam/                      # Roles, policies, boundaries
│       ├── eventbridge/              # Event bus
│       ├── sqs/                      # Encrypted queues
│       ├── dynamodb/                 # Encrypted tables
│       ├── cloudtrail/               # Audit logging
│       ├── config/                   # Compliance rules
│       ├── budgets/                  # Cost management
│       ├── cloudwatch/               # Monitoring
│       └── waf/                      # Web Application Firewall
├── environments/                     # Environment configs
│   ├── dev.tfvars
│   ├── staging.tfvars
│   └── prod.tfvars
├── policies/                         # IAM policy documents
├── scripts/                          # Build and deploy
├── tests/                            # Unit, integration, security tests
└── docs/                             # Documentation
```

## Prerequisites

- **Python 3.12+**
- **pip** or **uv** for package management
- **Terraform 1.5+**
- **AWS CLI** configured with credentials
- **AWS Account** with admin permissions

## Quick Start

### 1. Clone and Setup

```bash
cd aws-serverless

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure Environment

```bash
cd terraform

# Copy example variables for your environment
cp ../environments/dev.tfvars terraform.tfvars

# Edit as needed
vim terraform.tfvars
```

### 3. Deploy Infrastructure

```bash
# Deploy to dev environment
./scripts/deploy.sh --env dev

# Or manually
terraform init
terraform plan -var-file=../environments/dev.tfvars
terraform apply -var-file=../environments/dev.tfvars
```

### 4. Test the API

```bash
# Get Cognito token
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id $CLIENT_ID \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=$USER,PASSWORD=$PASS \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Call API
curl -H "Authorization: Bearer $TOKEN" \
  https://your-api-id.execute-api.eu-central-2.amazonaws.com/dev/resource
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region | eu-central-2 |
| `ENVIRONMENT` | Environment name | dev |
| `LOG_LEVEL` | Logging level | INFO |
| `TENANT_TABLE` | DynamoDB table name | - |
| `KMS_KEY_ID` | KMS key for encryption | - |

### Terraform Variables

```hcl
# environments/prod.tfvars
aws_region          = "eu-central-2"
environment         = "prod"
project_name        = "enterprise-api"

# VPC
vpc_cidr            = "10.1.0.0/16"
enable_nat_gateway  = true
multi_az            = true

# Security
enable_waf          = true
enable_guardduty    = true
mfa_required        = true

# Compliance
enable_cloudtrail   = true
enable_config       = true

# Cost
budget_limit        = 5000
```

## Lambda Functions

| Function | Trigger | Description |
|----------|---------|-------------|
| `api-handler` | API Gateway | Main API business logic |
| `authorizer` | API Gateway | JWT validation and policy generation |
| `async-processor` | SQS | Batch message processing |
| `event-router` | EventBridge | Cross-account event handling |
| `secret-rotation` | Secrets Manager | Automatic credential rotation |
| `audit-handler` | CloudWatch Logs | Security event processing |
| `scheduled-task` | EventBridge | Periodic maintenance jobs |

## AWS Services

| Category | Services |
|----------|----------|
| **Compute** | Lambda (VPC-enabled) |
| **API** | API Gateway (REST), Lambda Authorizer |
| **Auth** | Cognito User Pools, Identity Pools |
| **Security** | WAF, KMS, Secrets Manager, Parameter Store |
| **Network** | VPC, Subnets, NAT Gateway, VPC Endpoints |
| **Storage** | S3, DynamoDB (encrypted) |
| **Messaging** | SQS, SNS, EventBridge |
| **Compliance** | CloudTrail, AWS Config, GuardDuty |
| **Monitoring** | CloudWatch, X-Ray |
| **Cost** | Budgets, Cost Allocation Tags |

## Security Best Practices

### IAM
- Permission boundaries on all roles
- Least privilege policies
- No wildcard actions/resources
- Cross-account access with external ID

### Data Protection
- KMS encryption for all data at rest
- TLS 1.2+ for data in transit
- Secrets Manager for credentials
- No secrets in environment variables

### Network
- Lambdas in private subnets
- VPC endpoints for AWS services
- Security groups with minimal rules
- No public IPs on resources

### API
- WAF with managed rule groups
- Rate limiting per API key
- Request validation
- Access logging enabled

## Development

### Running Tests

```bash
# All tests
./scripts/test.sh

# Unit tests only
pytest tests/unit -v

# Security tests
pytest tests/security -v

# With coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Linting
ruff check src tests

# Type checking
mypy src

# Security scan
bandit -r src
```

### Local Development

```bash
# Run with SAM CLI
sam local invoke ApiHandler --event events/api_event.json

# Or use moto for AWS mocking
pytest tests/integration -v
```

## Multi-Environment Deployment

```bash
# Dev (minimal security, cost-optimized)
./scripts/deploy.sh --env dev

# Staging (production-like security)
./scripts/deploy.sh --env staging

# Production (full security + compliance)
./scripts/deploy.sh --env prod
```

## Cost Considerations

| Feature | Dev | Staging | Prod |
|---------|-----|---------|------|
| NAT Gateway | No | Yes | Yes (Multi-AZ) |
| WAF | No | Yes | Yes |
| GuardDuty | No | No | Yes |
| Config Rules | No | Yes | Yes |
| Multi-AZ | No | No | Yes |

**Estimated Monthly Cost:**
- Dev: ~$50-100
- Staging: ~$200-400
- Prod: ~$500-1000+

## Cleanup

```bash
# Destroy specific environment
./scripts/deploy.sh --env dev --destroy

# Or manually
terraform destroy -var-file=../environments/dev.tfvars
```

## Documentation

- [Architecture Guide](docs/architecture.md)
- [Security Best Practices](docs/security.md)
- [Operational Runbook](docs/runbook.md)
- [API Reference](docs/api-reference.md)

## License

This project is for educational and demonstration purposes.
