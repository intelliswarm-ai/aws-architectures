# Secure ML Data Transformation Pipeline

A secure, VPC-isolated data transformation pipeline for financial ML fraud detection using AWS Glue, DataBrew, and custom PySpark transformations. Designed for financial institutions with strict compliance requirements.

## Architecture

```
                                    VPC (No Internet Gateway)
    +------------------------------------------------------------------------+
    |                                                                        |
    |  +----------------+     +------------------+     +------------------+  |
    |  |   S3 Bucket    |     |   Glue DataBrew  |     |  Glue ETL Job    |  |
    |  | (Raw Data)     |---->| (PII Detection)  |---->| (PySpark)        |  |
    |  +----------------+     +------------------+     +------------------+  |
    |                                                           |            |
    |  +----------------+     +------------------+     +--------v---------+  |
    |  | CloudWatch     |<----| Glue Catalog     |<----| S3 Bucket        |  |
    |  | (Audit Logs)   |     | (Data Lineage)   |     | (Transformed)    |  |
    |  +----------------+     +------------------+     +------------------+  |
    |                                                                        |
    +------------------------------------------------------------------------+
                    |                                        |
                    v                                        v
            VPC Endpoints                            VPC Endpoints
            (S3, Glue, CloudWatch, KMS)              (No Internet Access)
```

## Features

### Data Transformation Capabilities

- **PII Tokenization**: Secure tokenization of personally identifiable information using deterministic and non-deterministic methods
- **Transaction Amount Binning**: Statistical distribution-based binning (percentile, quantile, custom ranges)
- **Merchant Category Encoding**: Custom mapping with hierarchical category support and unknown handling
- **Anomaly Flagging**: Isolation Forest implementation for real-time anomaly detection

### Security & Compliance

- **VPC Isolation**: All processing occurs within a VPC with no internet gateway
- **VPC Endpoints**: Private connectivity to AWS services (S3, Glue, CloudWatch, KMS)
- **Data Encryption**: KMS encryption for data at rest and in transit
- **Audit Trails**: Comprehensive logging to encrypted CloudWatch Logs
- **Data Lineage**: Glue job bookmarks and catalog for complete data lineage tracking

### AWS Services Used

| Service | Purpose |
|---------|---------|
| AWS Glue ETL | PySpark-based data transformations |
| AWS Glue DataBrew | Sensitive data detection and profiling |
| AWS Glue Data Catalog | Metadata management and lineage |
| Amazon S3 | Data storage (raw, processed, archived) |
| AWS KMS | Encryption key management |
| Amazon CloudWatch | Audit logging and monitoring |
| AWS VPC | Network isolation |

## Project Structure

```
secure-ml-transformation/
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
├── cloudformation/
│   ├── deploy-cfn.sh
│   ├── main.yaml
│   └── nested/
│       ├── cloudwatch.yaml
│       ├── glue.yaml
│       ├── iam.yaml
│       ├── kms.yaml
│       ├── s3.yaml
│       └── vpc.yaml
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars
│   └── modules/
│       ├── cloudwatch/
│       ├── glue/
│       ├── iam/
│       ├── kms/
│       ├── s3/
│       └── vpc/
├── sam/
│   ├── samconfig.toml
│   └── template.yaml
├── src/
│   ├── common/
│   │   ├── __init__.py
│   │   ├── clients.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── models.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── job_trigger_handler.py
│   │   ├── lineage_handler.py
│   │   └── audit_handler.py
│   └── services/
│       ├── __init__.py
│       ├── glue_service.py
│       ├── databrew_service.py
│       ├── lineage_service.py
│       └── audit_service.py
├── glue/
│   └── jobs/
│       ├── pii_tokenization.py
│       ├── amount_binning.py
│       ├── merchant_encoding.py
│       ├── anomaly_detection.py
│       └── main_etl.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── docs/
│   ├── BUSINESS_LOGIC.md
│   └── COST_SIMULATION.md
└── scripts/
    ├── build.sh
    ├── deploy.sh
    ├── destroy.sh
    └── test.sh
```

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.12+
- Terraform >= 1.5.0 (for Terraform deployment)
- AWS SAM CLI (for SAM deployment)

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for deployment | `eu-central-2` |
| `ENVIRONMENT` | Deployment environment | `dev` |
| `PROJECT_NAME` | Project name prefix | `secure-ml-transform` |
| `KMS_KEY_ALIAS` | KMS key alias for encryption | `alias/secure-ml-transform` |
| `LOG_RETENTION_DAYS` | CloudWatch log retention | `90` |

### Glue Job Parameters

| Parameter | Description |
|-----------|-------------|
| `--source_bucket` | S3 bucket for raw data |
| `--target_bucket` | S3 bucket for transformed data |
| `--pii_columns` | Comma-separated list of PII columns |
| `--binning_config` | JSON configuration for amount binning |
| `--merchant_mapping` | S3 path to merchant category mapping |
| `--anomaly_threshold` | Isolation Forest contamination parameter |

## Deployment

### Using Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan -var-file="terraform.tfvars"

# Apply the configuration
terraform apply -var-file="terraform.tfvars"
```

### Using CloudFormation

```bash
cd cloudformation
./deploy-cfn.sh dev eu-central-2
```

### Using SAM

```bash
cd sam
sam build
sam deploy --guided
```

## Data Transformation Pipeline

### 1. PII Tokenization

Sensitive fields are tokenized using deterministic hashing with salt:

```python
# Example configuration
pii_config = {
    "customer_id": {"method": "deterministic", "salt": "env_specific_salt"},
    "account_number": {"method": "format_preserving", "preserve_prefix": 4},
    "email": {"method": "hash", "algorithm": "sha256"}
}
```

### 2. Transaction Amount Binning

Statistical distribution-based binning:

```python
# Example configuration
binning_config = {
    "method": "percentile",
    "bins": [0, 10, 25, 50, 75, 90, 95, 99, 100],
    "labels": ["micro", "small", "low", "medium", "high", "large", "very_large", "extreme"]
}
```

### 3. Merchant Category Encoding

Custom hierarchical encoding with fallback:

```python
# Example mapping
merchant_mapping = {
    "5411": {"category": "grocery", "risk_level": "low", "parent": "retail"},
    "5812": {"category": "restaurant", "risk_level": "medium", "parent": "dining"},
    "unknown": {"category": "other", "risk_level": "high", "parent": "uncategorized"}
}
```

### 4. Anomaly Detection

Isolation Forest implementation:

```python
# Example parameters
anomaly_config = {
    "contamination": 0.01,
    "n_estimators": 100,
    "features": ["amount_bin", "merchant_risk", "time_delta", "velocity"]
}
```

## Security Considerations

### Network Isolation

- VPC with private subnets only (no NAT Gateway or Internet Gateway)
- VPC Endpoints for all AWS service communication
- Security groups restricting traffic to VPC endpoints only

### Data Protection

- Server-side encryption with customer-managed KMS keys
- TLS 1.2+ for all data in transit
- S3 bucket policies enforcing encryption
- No public access to any resources

### Audit & Compliance

- All Glue job executions logged to CloudWatch
- Job bookmarks provide transformation lineage
- CloudTrail integration for API audit
- Log encryption with KMS

## Monitoring

### CloudWatch Dashboards

- Job execution metrics (duration, records processed)
- Error rates and retry counts
- Data quality metrics
- Anomaly detection statistics

### Alarms

- Job failure notifications
- Data quality threshold breaches
- Anomaly rate spikes
- Processing latency alerts

## Testing

```bash
# Run all tests
./scripts/test.sh

# Run unit tests only
pytest tests/unit -v

# Run with coverage
pytest tests/ --cov=src --cov=glue --cov-report=html
```

## Cost Optimization

See [COST_SIMULATION.md](docs/COST_SIMULATION.md) for detailed cost analysis.

Key cost factors:
- Glue DPU hours
- S3 storage and requests
- CloudWatch log ingestion and storage
- KMS key operations

## References

- [AWS Glue VPC Configuration](https://docs.aws.amazon.com/glue/latest/dg/glue-vpc.html)
- [AWS Glue DataBrew Documentation](https://docs.aws.amazon.com/databrew/latest/dg/what-is.html)
- [AWS Glue Job Bookmarks](https://docs.aws.amazon.com/glue/latest/dg/monitor-continuations.html)
- [VPC Endpoints for AWS Glue](https://docs.aws.amazon.com/glue/latest/dg/vpc-endpoints.html)

## License

This project is for educational and demonstration purposes.
