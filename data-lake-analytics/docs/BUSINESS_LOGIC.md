# AWS Athena Data Lake - Business Logic

This document describes the business logic and technical implementation details for the AWS Athena Data Lake Analytics Platform.

## Table of Contents

1. [Data Lake Architecture](#data-lake-architecture)
2. [Data Flow](#data-flow)
3. [Format Transformation (JSON to Parquet)](#format-transformation-json-to-parquet)
4. [Lake Formation Security Model](#lake-formation-security-model)
5. [Partitioning Strategy](#partitioning-strategy)
6. [Query Optimization](#query-optimization)
7. [Cost Management](#cost-management)
8. [Operational Patterns](#operational-patterns)

---

## Data Lake Architecture

### Overview

The data lake follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Data Lake Architecture                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   Raw Zone   │───▶│ Processed    │───▶│  Analytics   │               │
│  │   (JSON)     │    │   Zone       │    │    Zone      │               │
│  │              │    │  (Parquet)   │    │              │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│         │                   │                   │                       │
│         ▼                   ▼                   ▼                       │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │                    AWS Glue Data Catalog                     │       │
│  │              (Tables, Schemas, Partitions)                   │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                              │                                          │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │                    AWS Lake Formation                        │       │
│  │           (Fine-grained Access Control, LF-Tags)             │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Zones

| Zone | Format | Purpose | Retention |
|------|--------|---------|-----------|
| Raw | JSON (NDJSON) | Original ingested data | 1 year, Glacier after 90 days |
| Processed | Parquet (Snappy) | Optimized for queries | Indefinite, IA after 30 days |
| Results | Mixed | Query results, scripts | 7 days for results |

---

## Data Flow

### 1. Data Ingestion

```
External Sources → Lambda (Ingest) → S3 Raw Bucket
       │
       ├── API Gateway / Lambda Function URL (POST /ingest)
       ├── Kinesis Data Streams
       └── Direct S3 Upload
```

**Ingest Handler Logic:**

1. Receive documents (JSON array or Kinesis records)
2. Validate document schema (EventDocument model)
3. Determine partition from document timestamp
4. Write as Newline-Delimited JSON (NDJSON) to S3
5. Return ingestion result with record count and S3 location

**Document Schema:**

```json
{
  "event_id": "uuid",
  "timestamp": "ISO-8601",
  "event_type": "string",
  "user_id": "string",
  "session_id": "string (optional)",
  "properties": { "key": "value" },
  "geo": {
    "country": "string",
    "city": "string",
    "lat": "number",
    "lon": "number"
  }
}
```

### 2. ETL Processing

```
S3 Raw Bucket → Glue ETL Job → S3 Processed Bucket
       │
       ├── Scheduled (EventBridge - hourly)
       ├── Event-driven (S3 trigger)
       └── On-demand (API/Lambda)
```

**ETL Job Logic:**

1. Read JSON files from source partition
2. Add partition columns (year, month, day, hour)
3. Cast timestamp fields to proper types
4. Apply schema mapping for consistent types
5. Write as Parquet with Snappy compression
6. Update Glue Data Catalog

### 3. Query Execution

```
User Request → Lambda (Query) → Athena → S3 (Processed)
                                    │
                                    └──→ S3 (Results)
```

**Query Handler Logic:**

1. Validate query syntax and permissions
2. Submit query to Athena workgroup
3. Optionally wait for completion (async or sync mode)
4. Return execution ID and status
5. Fetch results with pagination if requested

---

## Format Transformation (JSON to Parquet)

### Why Parquet?

Apache Parquet provides significant advantages for analytical workloads:

| Metric | JSON | Parquet (Snappy) | Improvement |
|--------|------|------------------|-------------|
| Storage Size | 100 MB | ~17 MB | 6x reduction |
| Query Time | 10 seconds | 2 seconds | 5x faster |
| Data Scanned | 100 MB | 5 MB* | 20x reduction* |
| Cost per Query | $0.0005 | $0.000025* | 20x cheaper* |

*With proper column selection (predicate pushdown)

### Columnar Storage Benefits

```
Row-based (JSON):
┌────────┬───────────┬───────────┬─────────┐
│ event_id│ timestamp │ event_type│ user_id │  → Read entire row
├────────┼───────────┼───────────┼─────────┤
│ uuid-1  │ 2024-01-01│ click     │ user-1  │
│ uuid-2  │ 2024-01-01│ view      │ user-2  │
└────────┴───────────┴───────────┴─────────┘

Columnar (Parquet):
┌────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐
│event_id│ │ timestamp │ │ event_type│ │ user_id │  → Read only needed columns
├────────┤ ├───────────┤ ├───────────┤ ├─────────┤
│ uuid-1 │ │ 2024-01-01│ │ click     │ │ user-1  │
│ uuid-2 │ │ 2024-01-01│ │ view      │ │ user-2  │
└────────┘ └───────────┘ └───────────┘ └─────────┘
```

### Snappy Compression

- **Fast compression/decompression** (optimized for speed over ratio)
- **Splittable** - allows parallel processing
- **~6x compression ratio** for typical JSON data
- **No decompression overhead** for columnar access

### Predicate Pushdown

Athena pushes filter predicates down to the storage layer:

```sql
-- This query only reads the event_type column
SELECT event_type, COUNT(*)
FROM events
WHERE year = '2024' AND month = '01'
GROUP BY event_type
```

Instead of scanning 100MB of data, Athena:
1. Uses partition pruning (year/month) to skip partitions
2. Reads only the `event_type` column (~5MB)
3. Applies row group statistics for further pruning

---

## Lake Formation Security Model

### Permission Hierarchy

```
IAM Permissions (coarse-grained)
         │
         ▼
Lake Formation Permissions (fine-grained)
         │
         ├── Database Level
         │      └── CREATE_TABLE, DESCRIBE, ALTER, DROP
         │
         ├── Table Level
         │      └── SELECT, INSERT, DELETE, DESCRIBE, ALTER
         │
         ├── Column Level
         │      └── SELECT on specific columns
         │
         └── Data Location
               └── DATA_LOCATION_ACCESS
```

### Critical IAM Permission: lakeformation:GetDataAccess

**Why it's required:**

When Lake Formation manages data access, it intercepts S3 requests. Principals need:

1. **Lake Formation permissions** (SELECT on table)
2. **IAM permission**: `lakeformation:GetDataAccess`

Without `lakeformation:GetDataAccess`, even with proper LF permissions, queries fail with:

```
User: arn:aws:iam::123456789012:role/MyRole is not authorized
to perform: lakeformation:GetDataAccess
```

**How it works:**

```
Query Request → Lake Formation → Check Permissions
                      │
                      ├── LF Permission? ✓
                      ├── GetDataAccess IAM? ✓
                      │
                      ▼
              Temporary Credentials → S3 Access
```

### Data Location Registration

Before Lake Formation can manage access:

```python
# Register S3 location with Lake Formation
lakeformation.register_resource(
    ResourceArn="s3://my-bucket/processed/",
    RoleArn="arn:aws:iam::123456789012:role/LakeFormationRole"
)
```

Then grant data location access:

```python
lakeformation.grant_permissions(
    Principal={"DataLakePrincipalIdentifier": role_arn},
    Resource={"DataLocation": {"ResourceArn": "s3://my-bucket/processed/"}},
    Permissions=["DATA_LOCATION_ACCESS"]
)
```

### LF-Tags for Attribute-Based Access Control

```python
# Create tag
lakeformation.create_lf_tag(
    TagKey="DataSensitivity",
    TagValues=["public", "internal", "confidential", "restricted"]
)

# Assign to table
lakeformation.add_lf_tags_to_resource(
    Resource={"Table": {"DatabaseName": "analytics_db", "Name": "events"}},
    LFTags=[{"TagKey": "DataSensitivity", "TagValues": ["internal"]}]
)

# Grant based on tag
lakeformation.grant_permissions(
    Principal={"DataLakePrincipalIdentifier": role_arn},
    Resource={"LFTagPolicy": {
        "ResourceType": "TABLE",
        "Expression": [{"TagKey": "DataSensitivity", "TagValues": ["internal"]}]
    }},
    Permissions=["SELECT"]
)
```

---

## Partitioning Strategy

### Time-Based Partitioning

```
s3://bucket/processed/
    └── year=2024/
        └── month=01/
            └── day=15/
                └── hour=14/
                    └── data_00001.parquet
```

### Partition Projection (Glue)

Instead of scanning partition metadata, Athena calculates partitions:

```sql
-- Table properties enable partition projection
projection.enabled = 'true'
projection.year.type = 'integer'
projection.year.range = '2020,2030'
projection.month.type = 'integer'
projection.month.range = '1,12'
projection.month.digits = '2'
storage.location.template = 's3://bucket/processed/year=${year}/month=${month}/day=${day}/hour=${hour}'
```

**Benefits:**
- No MSCK REPAIR TABLE needed
- No partition metadata queries
- Instant partition discovery

### Partition Sizing Guidelines

| Data Volume | Recommended Partition | Reasoning |
|-------------|----------------------|-----------|
| < 100 MB/hour | Daily | Avoid small file overhead |
| 100 MB - 1 GB/hour | Hourly | Balanced granularity |
| > 1 GB/hour | Hourly with bucketing | Manage file count |

---

## Query Optimization

### Best Practices

1. **Always filter by partition columns first**

```sql
-- Good: Partition pruning
SELECT * FROM events
WHERE year = '2024' AND month = '01' AND day = '15'
  AND event_type = 'click'

-- Bad: Full table scan
SELECT * FROM events
WHERE event_type = 'click'
```

2. **Select only needed columns**

```sql
-- Good: Reads ~5% of data
SELECT event_type, COUNT(*) FROM events
GROUP BY event_type

-- Bad: Reads 100% of data
SELECT * FROM events
```

3. **Use approximate functions for large datasets**

```sql
-- Good: Faster for large cardinality
SELECT approx_distinct(user_id) FROM events

-- Slower: Exact count
SELECT COUNT(DISTINCT user_id) FROM events
```

### Query Cost Estimation

```python
# Athena pricing: $5 per TB scanned
def calculate_cost(data_scanned_bytes: int, price_per_tb: float = 5.0) -> float:
    tb_scanned = data_scanned_bytes / (1024 ** 4)
    return tb_scanned * price_per_tb

# Example: 10 GB scan = $0.05
cost = calculate_cost(10 * 1024**3)  # 10 GB → $0.05
```

---

## Cost Management

### Athena Cost Controls

1. **Workgroup byte limit**: Maximum bytes scanned per query

```hcl
bytes_scanned_cutoff_per_query = 10737418240  # 10 GB
```

2. **Result reuse**: Cache query results (Athena automatically caches for 24h)

3. **Query scheduling**: Run expensive queries during off-peak

### Storage Cost Optimization

| Storage Class | Use Case | Cost (per GB/month) |
|--------------|----------|---------------------|
| S3 Standard | Hot data (< 30 days) | $0.023 |
| S3 Standard-IA | Warm data (30-180 days) | $0.0125 |
| S3 Glacier | Cold data (> 180 days) | $0.004 |

### Glue ETL Cost

- **DPU-hour**: $0.44
- **Minimum**: 10 DPUs, 1 minute minimum
- **Optimization**: Use Glue 4.0 with auto-scaling

---

## Operational Patterns

### Scheduled ETL (Hourly)

```
EventBridge (rate(1 hour))
         │
         ▼
Lambda ETL Handler
         │
    ├── Get previous hour partition
    ├── Start Glue job with partition args
    └── Return job_run_id
         │
         ▼
Glue ETL Job
    ├── Read JSON from raw/year=X/month=Y/day=Z/hour=H/
    ├── Transform to Parquet
    └── Write to processed/year=X/month=Y/day=Z/hour=H/
```

### On-Demand Query Pattern

```python
# Async pattern (recommended for long queries)
execution = athena.execute_query(
    query="SELECT ...",
    wait=False  # Don't block
)

# Poll for completion
while True:
    status = athena.get_query_execution(execution.query_execution_id)
    if status.state in ('SUCCEEDED', 'FAILED', 'CANCELLED'):
        break
    time.sleep(1)

# Get results
if status.state == 'SUCCEEDED':
    results = athena.get_query_results(execution.query_execution_id)
```

### Data Quality Monitoring

```sql
-- Daily data quality check
SELECT
  year, month, day,
  COUNT(*) as total_records,
  COUNT(CASE WHEN event_id IS NULL THEN 1 END) as null_event_ids,
  COUNT(CASE WHEN user_id IS NULL THEN 1 END) as null_user_ids,
  COUNT(DISTINCT event_type) as unique_event_types
FROM events
GROUP BY year, month, day
ORDER BY year DESC, month DESC, day DESC
LIMIT 30
```

### Backfill Pattern

```python
# Process historical data by partition
from datetime import datetime, timedelta

def backfill(start_date: datetime, end_date: datetime):
    current = start_date
    while current <= end_date:
        partition = PartitionSpec.from_datetime(current)

        # Trigger ETL for this partition
        glue.start_etl_job(arguments={
            "--partition_year": partition.year,
            "--partition_month": partition.month,
            "--partition_day": partition.day,
            "--partition_hour": partition.hour,
        })

        current += timedelta(hours=1)
```

---

## References

- [Amazon Athena Best Practices](https://docs.aws.amazon.com/athena/latest/ug/performance-tuning.html)
- [AWS Lake Formation Developer Guide](https://docs.aws.amazon.com/lake-formation/latest/dg/)
- [Apache Parquet Documentation](https://parquet.apache.org/docs/)
- [AWS Glue ETL Best Practices](https://docs.aws.amazon.com/glue/latest/dg/best-practices.html)
