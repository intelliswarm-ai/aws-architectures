# AWS Athena Data Lake Analytics

A high-performance analytics solution using Amazon Athena with Apache Parquet optimization, AWS Glue ETL, and AWS Lake Formation for security and governance.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                       DATA LAKE ANALYTICS PLATFORM                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │                         Data Ingestion Layer                                 │  │
│   │                                                                              │  │
│   │  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────────┐ │  │
│   │  │ Application │────▶│   Lambda    │────▶│      S3 Raw Zone               │ │  │
│   │  │ (JSON docs) │     │  (Ingest)   │     │   s3://datalake/raw/json/       │ │  │
│   │  └─────────────┘     └─────────────┘     │   - Partitioned by date         │ │  │
│   │                                          │   - Hundreds of files/hour      │ │  │
│   │                                          └─────────────────────────────────┘ │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                            │
│                                        ▼                                            │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │                         ETL Processing Layer                                 │  │
│   │                                                                              │  │
│   │  ┌─────────────────────────────────────────────────────────────────────────┐ │  │
│   │  │                        AWS Glue                                         │ │  │
│   │  │                                                                         │ │  │
│   │  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │ │  │
│   │  │  │   Crawler   │    │  ETL Job    │    │  Crawler    │                  │ │  │
│   │  │  │  (Raw JSON) │───▶│  JSON →     │───▶│ (Parquet)   │                 │ │  │
│   │  │  │             │    │  Parquet    │    │             │                  │ │  │
│   │  │  └─────────────┘    └─────────────┘    └─────────────┘                  │ │  │
│   │  │                                                                         │ │  │
│   │  │  Transformations:                                                       │ │  │
│   │  │  - Convert JSON to Parquet (columnar)                                   │ │  │
│   │  │  - Apply Snappy compression                                             │ │  │
│   │  │  - Partition by year/month/day/hour                                     │ │  │
│   │  │  - Schema evolution handling                                            │ │  │
│   │  │                                                                         │ │  │
│   │  └─────────────────────────────────────────────────────────────────────────┘ │  │
│   │                                        │                                     │  │
│   │                                        ▼                                     │  │
│   │  ┌─────────────────────────────────────────────────────────────────────────┐ │  │
│   │  │                    S3 Processed Zone                                    │ │  │
│   │  │              s3://datalake/processed/parquet/                           │ │  │
│   │  │                                                                         │ │  │
│   │  │  - Columnar format (Parquet)                                            │ │  │
│   │  │  - Snappy compression (6x smaller)                                      │ │  │
│   │  │  - Partitioned: year=2024/month=01/day=15/hour=10/                      │ │  │
│   │  │  - Predicate pushdown enabled                                           │ │  │
│   │  │                                                                         │ │  │
│   │  └─────────────────────────────────────────────────────────────────────────┘ │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                            │
│                                        ▼                                            │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │                     Data Catalog & Security Layer                            │  │
│   │                                                                              │  │
│   │  ┌─────────────────────────────────┐  ┌─────────────────────────────────────┐│  │
│   │  │       AWS Glue Data Catalog     │  │       AWS Lake Formation            ││  │
│   │  │                                 │  │                                     ││  │
│   │  │  Database: analytics_db         │  │  - S3 locations registered          ││  │
│   │  │  ├── raw_events (JSON)          │  │  - Data location permissions        ││  │
│   │  │  └── events (Parquet)           │  │  - Table/column-level access        ││  │
│   │  │                                 │  │  - lakeformation:GetDataAccess      ││  │
│   │  │  Schema Registry                │  │  - Fine-grained access control      ││  │
│   │  │  Partition metadata             │  │                                     ││  │
│   │  │                                 │  │                                     ││  │
│   │  └─────────────────────────────────┘  └─────────────────────────────────────┘│  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                            │
│                                        ▼                                            │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │                         Analytics Layer                                      │  │
│   │                                                                              │  │
│   │  ┌─────────────────────────────────────────────────────────────────────────┐ │  │
│   │  │                       Amazon Athena                                     │ │  │
│   │  │                                                                         │ │  │
│   │  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │ │  │
│   │  │  │   Workgroup │    │   Queries   │    │   Results   │                  │ │  │
│   │  │  │  analytics  │    │  (Presto)   │    │   S3 bucket │                  │ │  │
│   │  │  └─────────────┘    └─────────────┘    └─────────────┘                  │ │  │
│   │  │                                                                         │ │  │
│   │  │  Performance Benefits (Parquet):                                        │ │  │
│   │  │  - 2-10x faster queries                                                 │ │  │
│   │  │  - 90% less data scanned                                                │ │  │
│   │  │  - Predicate pushdown                                                   │ │  │
│   │  │  - Column pruning                                                       │ │  │
│   │  │                                                                         │ │  │
│   │  └─────────────────────────────────────────────────────────────────────────┘ │  │
│   │                                                                              │  │
│   │  ┌─────────────────────────────────────────────────────────────────────────┐ │  │
│   │  │                    Data Analytics Consumers                             │ │  │
│   │  │                                                                         │ │  │
│   │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │  │
│   │  │  │  QuickSight │  │  Redshift   │  │   Jupyter   │  │    API      │     │ │  │
│   │  │  │  Dashboards │  │  Spectrum   │  │  Notebooks  │  │  (Lambda)   │     │ │  │
│   │  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │ │  │
│   │  │                                                                         │ │  │
│   │  └─────────────────────────────────────────────────────────────────────────┘ │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Features

- **JSON to Parquet Transformation**: Glue ETL converts JSON to columnar Parquet format
- **Compression**: Snappy compression reduces storage by 6x
- **Partitioning**: Time-based partitions (year/month/day/hour) for efficient queries
- **Predicate Pushdown**: Skip irrelevant data blocks using column statistics
- **Lake Formation Security**: Fine-grained access control with `lakeformation:GetDataAccess`
- **Cost Optimization**: Pay only for data scanned (90% reduction with Parquet)
- **Schema Evolution**: Handle schema changes gracefully

## Use Case

A company loads hundreds of JSON documents into S3 every hour. The Data Analytics team uses Athena for analysis, but queries are slow due to:
- Row-based JSON format requiring full file scans
- No compression increasing data transfer
- No partitioning causing full table scans
- Large data volumes (hundreds of files/hour)

**Solution**: Transform to Parquet with partitioning and Lake Formation governance.

## Project Structure

```
aws-athena/
├── README.md
├── pyproject.toml
├── src/
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── ingest_handler.py         # S3 ingestion trigger
│   │   ├── etl_trigger_handler.py    # Trigger Glue ETL job
│   │   ├── query_handler.py          # Execute Athena queries
│   │   └── api_handler.py            # REST API for analytics
│   ├── services/
│   │   ├── __init__.py
│   │   ├── glue_service.py           # Glue job management
│   │   ├── athena_service.py         # Athena query execution
│   │   ├── lakeformation_service.py  # Lake Formation permissions
│   │   └── s3_service.py             # S3 operations
│   └── common/
│       ├── __init__.py
│       ├── models.py                 # Pydantic data models
│       ├── config.py                 # Configuration settings
│       └── exceptions.py             # Custom exceptions
├── glue/
│   └── etl_job.py                    # Glue ETL script (JSON → Parquet)
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
│       ├── s3/                       # Data lake buckets
│       ├── glue/                     # Crawlers, ETL jobs, catalog
│       ├── athena/                   # Workgroups, query results
│       ├── lakeformation/            # Data lake security
│       ├── lambda/                   # Lambda functions
│       ├── iam/                      # Roles & policies
│       └── cloudwatch/               # Monitoring
├── cloudformation/
│   ├── main.yaml
│   ├── deploy-cfn.sh
│   └── nested/
│       ├── s3.yaml
│       ├── glue.yaml
│       ├── athena.yaml
│       ├── lakeformation.yaml
│       ├── lambda.yaml
│       ├── iam.yaml
│       └── cloudwatch.yaml
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   ├── build.sh
│   ├── deploy.sh
│   ├── test.sh
│   └── destroy.sh
└── docs/
    └── BUSINESS_LOGIC.md
```

## Performance Comparison

### JSON vs Parquet

| Metric | JSON (Before) | Parquet (After) | Improvement |
|--------|---------------|-----------------|-------------|
| Query Time | 45 seconds | 4 seconds | 11x faster |
| Data Scanned | 10 GB | 0.8 GB | 92% reduction |
| Storage Size | 10 GB | 1.6 GB | 84% reduction |
| Cost per Query | $0.05 | $0.004 | 92% savings |

### Why Parquet is Faster

```
JSON (Row-based):                    Parquet (Columnar):
┌─────────────────────────┐          ┌─────────┬─────────┬─────────┐
│ {"id":1,"name":"A",...} │          │ id      │ name    │ value   │
│ {"id":2,"name":"B",...} │          ├─────────┼─────────┼─────────┤
│ {"id":3,"name":"C",...} │          │ 1,2,3   │ A,B,C   │ x,y,z   │
│ ...                     │          │ (block) │ (block) │ (block) │
└─────────────────────────┘          └─────────┴─────────┴─────────┘

SELECT id FROM events                SELECT id FROM events
→ Must read ALL columns              → Read ONLY id column
→ Full file scan                     → Skip other columns
→ 10 GB scanned                      → 0.8 GB scanned
```

## Lake Formation Security

### Required IAM Permission

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lakeformation:GetDataAccess",
      "Resource": "*"
    }
  ]
}
```

### Access Control Hierarchy

```
Lake Formation Permissions:
│
├── Data Location Permissions
│   └── Grant access to S3 locations
│
├── Database Permissions
│   ├── CREATE_TABLE
│   ├── ALTER
│   └── DROP
│
├── Table Permissions
│   ├── SELECT (read data)
│   ├── INSERT (write data)
│   ├── DELETE
│   └── DESCRIBE (view schema)
│
└── Column Permissions
    └── SELECT on specific columns only
```

## Prerequisites

- Python 3.12+
- AWS CLI configured
- Terraform 1.5+ or AWS CloudFormation
- pip or uv for package management

## Quick Start

### 1. Deploy Infrastructure

#### Option A: Terraform

```bash
cd aws-athena

# Build and deploy
./scripts/build.sh
./scripts/deploy.sh -e dev
```

#### Option B: CloudFormation

```bash
cd aws-athena

# Deploy using CloudFormation
./cloudformation/deploy-cfn.sh -e dev -b my-deployment-bucket
```

### 2. Ingest Sample Data

```bash
# Upload JSON files to raw zone
aws s3 cp sample-data/ s3://datalake-dev-raw/events/year=2024/month=01/day=15/ --recursive
```

### 3. Run ETL Job

```bash
# Trigger Glue ETL job
aws glue start-job-run --job-name datalake-dev-json-to-parquet
```

### 4. Query with Athena

```sql
-- Query the optimized Parquet table
SELECT
    event_type,
    COUNT(*) as count,
    AVG(duration) as avg_duration
FROM analytics_db.events
WHERE year = '2024' AND month = '01'
GROUP BY event_type
ORDER BY count DESC
LIMIT 10;
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| RAW_BUCKET | S3 bucket for raw JSON data | - |
| PROCESSED_BUCKET | S3 bucket for Parquet data | - |
| GLUE_DATABASE | Glue catalog database name | analytics_db |
| ATHENA_WORKGROUP | Athena workgroup name | analytics |
| LOG_LEVEL | Logging level | INFO |

### Terraform Variables

```hcl
# terraform.tfvars
environment         = "dev"
aws_region          = "eu-central-2"
data_retention_days = 90
enable_encryption   = true
```

## Sample JSON Document

```json
{
  "event_id": "evt-12345",
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "page_view",
  "user_id": "user-67890",
  "session_id": "sess-abcde",
  "properties": {
    "page": "/products/widget",
    "referrer": "google.com",
    "duration": 45.2,
    "device": "mobile"
  },
  "geo": {
    "country": "US",
    "city": "New York",
    "latitude": 40.7128,
    "longitude": -74.0060
  }
}
```

## Partitioning Strategy

```
s3://datalake/processed/parquet/events/
├── year=2024/
│   ├── month=01/
│   │   ├── day=15/
│   │   │   ├── hour=00/
│   │   │   │   └── part-00000.snappy.parquet
│   │   │   ├── hour=01/
│   │   │   └── ...
│   │   └── day=16/
│   └── month=02/
└── year=2023/
```

**Query with partition pruning:**
```sql
-- Only scans data for January 2024
SELECT * FROM events
WHERE year = '2024' AND month = '01';
```

## Cost Considerations

| Service | Pricing |
|---------|---------|
| Athena | $5/TB scanned |
| S3 Storage | $0.023/GB/month |
| Glue ETL | $0.44/DPU-hour |
| Glue Crawler | $0.44/DPU-hour |
| Lake Formation | No additional charge |

**Cost Optimization Tips:**
- Use Parquet (90% less data scanned)
- Partition by frequently filtered columns
- Use workgroup query limits
- Enable query result reuse

## Security

- **Lake Formation**: Fine-grained access control
- **S3 Encryption**: SSE-S3 or SSE-KMS
- **IAM Policies**: Least privilege access
- **VPC Endpoints**: Private access to S3/Glue/Athena
- **CloudTrail**: Audit logging for data access

## Monitoring

CloudWatch dashboards provide:
- Glue job success/failure rates
- Athena query performance metrics
- S3 storage utilization
- Lambda invocation metrics
- Data ingestion throughput

## License

This project is for educational and demonstration purposes.
