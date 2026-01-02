# AWS Athena Data Lake - Cost Simulation

This document provides a detailed cost simulation for running the AWS Athena Data Lake architecture for one month. Costs are based on AWS pricing as of January 2025 for the **eu-central-2 (Zurich)** region.

## Table of Contents

1. [Scenario Overview](#scenario-overview)
2. [Cost Summary](#cost-summary)
3. [Detailed Cost Breakdown](#detailed-cost-breakdown)
4. [Cost Optimization Strategies](#cost-optimization-strategies)
5. [Scenario Comparisons](#scenario-comparisons)

---

## Scenario Overview

### Base Scenario: Medium-Volume Analytics Platform

| Metric | Value |
|--------|-------|
| **Data Ingestion** | 100 JSON documents/hour |
| **Average Document Size** | 5 KB |
| **Monthly Raw Data** | ~36 GB JSON |
| **Monthly Processed Data** | ~6 GB Parquet (6x compression) |
| **ETL Jobs** | 24/day (hourly) |
| **Athena Queries** | 500 queries/day |
| **Average Data Scanned/Query** | 100 MB |
| **Lambda Invocations** | ~50,000/month |
| **Users** | 10 analysts |

---

## Cost Summary

### Monthly Cost Estimate: Base Scenario

| Service | Monthly Cost (USD) | % of Total |
|---------|-------------------|------------|
| Amazon S3 | $2.45 | 4.2% |
| AWS Glue ETL | $31.68 | 54.5% |
| Amazon Athena | $7.50 | 12.9% |
| AWS Lambda | $0.52 | 0.9% |
| AWS Glue Data Catalog | $0.00 | 0.0% |
| AWS Lake Formation | $0.00 | 0.0% |
| CloudWatch | $3.50 | 6.0% |
| Data Transfer | $0.00 | 0.0% |
| **Miscellaneous** | $12.50 | 21.5% |
| **TOTAL** | **$58.15** | 100% |

```
┌────────────────────────────────────────────────────────────────┐
│                    Monthly Cost Distribution                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Glue ETL      ████████████████████████████░░░░░░░░░  54.5%    │
│  Miscellaneous ███████████░░░░░░░░░░░░░░░░░░░░░░░░░░  21.5%    │
│  Athena        ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  12.9%    │
│  CloudWatch    ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   6.0%    │
│  S3            ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   4.2%    │
│  Lambda        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0.9%    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Detailed Cost Breakdown

### 1. Amazon S3 Storage

#### Raw Data Bucket (JSON)

| Item | Calculation | Cost |
|------|-------------|------|
| Storage (first month) | 36 GB × $0.023/GB | $0.83 |
| PUT requests | 72,000 × $0.005/1000 | $0.36 |
| GET requests | 72,000 × $0.0004/1000 | $0.03 |
| **Subtotal** | | **$1.22** |

#### Processed Data Bucket (Parquet)

| Item | Calculation | Cost |
|------|-------------|------|
| Storage (Parquet) | 6 GB × $0.023/GB | $0.14 |
| PUT requests | 720 × $0.005/1000 | $0.00 |
| GET requests (Athena) | 15,000 × $0.0004/1000 | $0.01 |
| **Subtotal** | | **$0.15** |

#### Results Bucket (Athena)

| Item | Calculation | Cost |
|------|-------------|------|
| Storage (7-day retention) | 5 GB × $0.023/GB | $0.12 |
| PUT/GET requests | Included in Athena | $0.00 |
| **Subtotal** | | **$0.12** |

#### S3 Lifecycle Savings (Month 2+)

After 30 days, data transitions to cheaper storage:

| Tier | Data | Rate | Monthly Cost |
|------|------|------|--------------|
| Standard | 36 GB (current month) | $0.023/GB | $0.83 |
| Standard-IA | 36 GB (previous month) | $0.0125/GB | $0.45 |
| Glacier | 72 GB (90+ days) | $0.004/GB | $0.29 |

**S3 Monthly Total: $2.45** (growing to ~$3.50 after 6 months with lifecycle)

---

### 2. AWS Glue ETL

#### ETL Job Execution

| Item | Calculation | Cost |
|------|-------------|------|
| DPU-hours/job | 2 DPUs × 0.1 hours (6 min avg) | 0.2 DPU-hours |
| Jobs/month | 24 jobs/day × 30 days | 720 jobs |
| Total DPU-hours | 720 × 0.2 | 144 DPU-hours |
| Cost | 144 × $0.44/DPU-hour | $63.36 |
| **With Flex (50% discount)** | 144 × $0.22/DPU-hour | **$31.68** |

> **Note**: Using Glue Flex execution (50% cheaper) for non-time-sensitive ETL.

#### Glue Crawler (Optional)

| Item | Calculation | Cost |
|------|-------------|------|
| DPU-hours/run | 2 DPUs × 0.05 hours | 0.1 DPU-hours |
| Runs/month | 1 (on-demand) | 1 |
| Cost | 0.1 × $0.44 | **$0.04** |

#### Glue Data Catalog

| Item | Cost |
|------|------|
| First 1M objects stored | Free |
| First 1M requests/month | Free |
| **Subtotal** | **$0.00** |

**Glue Monthly Total: $31.68**

---

### 3. Amazon Athena

#### Query Costs

| Item | Calculation | Cost |
|------|-------------|------|
| Queries/month | 500 queries/day × 30 days | 15,000 queries |
| Avg data scanned/query | 100 MB (with Parquet optimization) | - |
| Total data scanned | 15,000 × 100 MB | 1.5 TB |
| Cost | 1.5 TB × $5/TB | **$7.50** |

#### Query Optimization Impact

Without Parquet optimization (raw JSON):

| Format | Data Scanned/Query | Monthly Cost |
|--------|-------------------|--------------|
| JSON (full scan) | 600 MB | $45.00 |
| Parquet (columnar) | 100 MB | $7.50 |
| **Savings** | 6x reduction | **$37.50/month** |

**Athena Monthly Total: $7.50**

---

### 4. AWS Lambda

#### Function Invocations

| Function | Invocations/Month | Avg Duration | Memory |
|----------|-------------------|--------------|--------|
| Ingest | 2,160 | 500 ms | 256 MB |
| ETL Trigger | 720 | 200 ms | 256 MB |
| Query | 15,000 | 300 ms | 256 MB |
| API | 30,000 | 200 ms | 256 MB |
| **Total** | 47,880 | - | - |

#### Cost Calculation

| Item | Calculation | Cost |
|------|-------------|------|
| Requests | 47,880 × $0.20/1M | $0.01 |
| Compute (GB-seconds) | | |
| - Ingest | 2,160 × 0.5s × 0.25 GB | 270 GB-s |
| - ETL | 720 × 0.2s × 0.25 GB | 36 GB-s |
| - Query | 15,000 × 0.3s × 0.25 GB | 1,125 GB-s |
| - API | 30,000 × 0.2s × 0.25 GB | 1,500 GB-s |
| Total GB-seconds | 2,931 GB-s | |
| Cost (after free tier) | 2,931 × $0.0000166667 | $0.05 |
| **Free Tier Credit** | -400,000 GB-s, -1M requests | -$0.00 |

> **Note**: Free tier (1M requests + 400K GB-seconds) covers most Lambda costs.

**Lambda Monthly Total: $0.52** (after free tier)

---

### 5. AWS Lake Formation

| Item | Cost |
|------|------|
| Data registration | Free |
| Permission management | Free |
| Tag-based access control | Free |
| **Total** | **$0.00** |

Lake Formation has no additional charges beyond the underlying services.

---

### 6. Amazon CloudWatch

#### Logs

| Item | Calculation | Cost |
|------|-------------|------|
| Log ingestion | 5 GB × $0.50/GB | $2.50 |
| Log storage | 5 GB × $0.03/GB | $0.15 |
| **Subtotal** | | **$2.65** |

#### Metrics & Alarms

| Item | Calculation | Cost |
|------|-------------|------|
| Custom metrics | 10 × $0.30/metric | $3.00 |
| Alarms | 5 × $0.10/alarm | $0.50 |
| Dashboard | 1 × $3.00 | $3.00 |
| **Subtotal** | | **$6.50** |

**CloudWatch Monthly Total: $3.50** (with free tier)

---

### 7. Miscellaneous Costs

| Item | Cost | Notes |
|------|------|-------|
| KMS (S3 encryption) | $1.00 | 1 CMK |
| KMS API requests | $0.50 | ~16,000 requests |
| EventBridge | $0.00 | First 14M events free |
| API Gateway (if used) | $10.00 | 1M requests |
| NAT Gateway (if VPC) | $0.00 | Not required |
| **Subtotal** | **$12.50** | |

---

## Cost Optimization Strategies

### 1. Glue ETL Optimization (Biggest Impact)

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Use Glue Flex | 50% | `--enable-flex` parameter |
| Reduce job frequency | Variable | Process every 4 hours instead of hourly |
| Auto-scaling workers | 20-30% | `--enable-auto-scaling` |
| Smaller worker type | Variable | G.1X instead of G.2X |

**Potential Glue Savings: $15-25/month**

### 2. Athena Query Optimization

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Partition pruning | 80-95% | Always filter by year/month/day |
| Column selection | 50-90% | SELECT only needed columns |
| Query result caching | 100% | Reuse cached results (24h) |
| Workgroup limits | Cost cap | Set BytesScannedCutoff |

**Example Query Cost Comparison:**

```sql
-- Bad: Full table scan ($5.00/query for 1TB table)
SELECT * FROM events WHERE event_type = 'click'

-- Good: Partition pruning + column selection ($0.05/query)
SELECT event_type, COUNT(*)
FROM events
WHERE year = '2024' AND month = '01' AND day = '15'
GROUP BY event_type
```

### 3. S3 Storage Optimization

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Lifecycle policies | 45-80% | Transition to IA/Glacier |
| Intelligent-Tiering | Auto | S3 Intelligent-Tiering class |
| Delete old results | 100% | 7-day lifecycle on results |
| Compression | 60-80% | Already using Snappy |

### 4. Reserved Capacity (High Volume)

For predictable workloads, consider:

| Service | Commitment | Discount |
|---------|------------|----------|
| S3 Storage Lens | 1 year | 25% |
| Athena Provisioned | Reserved | Up to 30% |
| Savings Plans | 1-3 years | Up to 72% |

---

## Scenario Comparisons

### Scenario 1: Small (Startup)

| Metric | Value |
|--------|-------|
| Data ingestion | 10 docs/hour |
| Monthly data | 3.6 GB |
| Queries | 50/day |
| **Monthly Cost** | **$12-18** |

### Scenario 2: Medium (Base Case)

| Metric | Value |
|--------|-------|
| Data ingestion | 100 docs/hour |
| Monthly data | 36 GB |
| Queries | 500/day |
| **Monthly Cost** | **$55-65** |

### Scenario 3: Large (Enterprise)

| Metric | Value |
|--------|-------|
| Data ingestion | 1,000 docs/hour |
| Monthly data | 360 GB |
| Queries | 5,000/day |
| **Monthly Cost** | **$350-450** |

### Scenario 4: Very Large (Big Data)

| Metric | Value |
|--------|-------|
| Data ingestion | 10,000 docs/hour |
| Monthly data | 3.6 TB |
| Queries | 50,000/day |
| **Monthly Cost** | **$2,500-3,500** |

---

## Cost Projection (12 Months)

### Base Scenario with Data Growth

| Month | Raw Data (Cumulative) | S3 Cost | Glue Cost | Athena Cost | Total |
|-------|----------------------|---------|-----------|-------------|-------|
| 1 | 36 GB | $2.45 | $31.68 | $7.50 | $58.15 |
| 2 | 72 GB | $3.20 | $31.68 | $7.50 | $58.90 |
| 3 | 108 GB | $3.65 | $31.68 | $7.50 | $59.35 |
| 4 | 144 GB (IA kicks in) | $3.90 | $31.68 | $7.50 | $59.60 |
| 6 | 216 GB | $4.20 | $31.68 | $7.50 | $59.90 |
| 12 | 432 GB (Glacier) | $4.80 | $31.68 | $7.50 | $60.50 |

**Annual Cost Estimate: ~$710**

---

## Cost Comparison: JSON vs Parquet

### Annual Cost Without Parquet Transformation

| Item | Cost |
|------|------|
| S3 Storage (JSON) | $100 (6x more storage) |
| Athena Queries | $540 (6x more scanned) |
| No Glue ETL | $0 |
| **Total** | **$640** |

### Annual Cost With Parquet Transformation

| Item | Cost |
|------|------|
| S3 Storage (Parquet) | $45 |
| Athena Queries | $90 |
| Glue ETL | $380 |
| **Total** | **$515** |

**Annual Savings: $125 (20%)** + much faster queries

> **Note**: At higher query volumes, Parquet savings increase dramatically. At 5,000 queries/day, annual savings exceed $4,000.

---

## Free Tier Summary

| Service | Free Tier (12 months) | Monthly Value |
|---------|----------------------|---------------|
| Lambda | 1M requests, 400K GB-s | ~$10 |
| S3 | 5 GB storage | $0.12 |
| Glue Data Catalog | 1M objects | ~$1 |
| CloudWatch | 10 custom metrics, 5 GB logs | ~$5 |
| EventBridge | 14M events | ~$14 |
| **Total Free Tier Value** | | **~$30/month** |

---

## Recommendations

1. **Use Glue Flex** for all non-time-critical ETL jobs (50% savings)
2. **Enforce partition filters** in Athena queries via workgroup policies
3. **Set BytesScannedCutoff** to prevent runaway query costs
4. **Enable S3 Lifecycle** policies from day one
5. **Monitor with CloudWatch** dashboards to identify optimization opportunities
6. **Consider Athena CTAS** for frequently-accessed query results

---

## References

- [AWS Pricing Calculator](https://calculator.aws/)
- [Amazon S3 Pricing](https://aws.amazon.com/s3/pricing/)
- [AWS Glue Pricing](https://aws.amazon.com/glue/pricing/)
- [Amazon Athena Pricing](https://aws.amazon.com/athena/pricing/)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
