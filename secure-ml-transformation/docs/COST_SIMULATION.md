# Cost Simulation

## Overview

This document provides cost estimates for the Secure ML Data Transformation Pipeline deployed in AWS Region eu-central-2 (Zurich).

## Assumptions

- **Data Volume**: 10 million transactions per day
- **Average Record Size**: 1 KB
- **Processing Frequency**: Daily batch processing
- **Retention Period**: 90 days for processed data, 365 days for audit logs
- **Environment**: Production workload

## Monthly Cost Breakdown

### AWS Glue

| Component | Units | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| ETL Job (DPU-hours) | 300 hrs | $0.44/DPU-hr | $132.00 |
| DataBrew Sessions | 100 hrs | $1.00/session | $100.00 |
| Data Catalog Storage | 1 GB | $1.00/100K objects | $10.00 |
| Crawler Runs | 60 runs | $0.44/DPU-hr (min 10 min) | $26.40 |
| **Glue Subtotal** | | | **$268.40** |

#### Calculation Details

**ETL Job Hours:**
- Daily run: ~1 hour at 10 DPUs = 10 DPU-hours
- 30 days × 10 DPU-hours = 300 DPU-hours/month

**DataBrew Sessions:**
- Profiling jobs: 2 hours/day × 30 days = 60 hours
- Recipe jobs: ~40 hours/month for ad-hoc analysis

### Amazon S3

| Component | Units | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| Raw Data Storage | 300 GB | $0.024/GB | $7.20 |
| Processed Data Storage | 300 GB | $0.024/GB | $7.20 |
| Archive Storage (S3 IA) | 2 TB | $0.0135/GB | $27.00 |
| PUT/COPY/POST Requests | 10M | $0.0055/1K | $55.00 |
| GET/SELECT Requests | 50M | $0.00044/1K | $22.00 |
| **S3 Subtotal** | | | **$118.40** |

#### Calculation Details

**Storage:**
- Daily data: 10M records × 1KB = 10 GB
- Raw retention (30 days): 300 GB
- Processed retention (30 days): 300 GB (similar size after transformation)
- Archive (90 days): ~2 TB in Infrequent Access

### AWS KMS

| Component | Units | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| Customer Managed Key | 1 key | $1.00/month | $1.00 |
| API Requests (Encrypt/Decrypt) | 20M | $0.03/10K | $60.00 |
| **KMS Subtotal** | | | **$61.00** |

#### Calculation Details

- Each record encrypted: 10M × 30 days = 300M operations
- With caching and batching, actual API calls: ~20M/month

### Amazon CloudWatch

| Component | Units | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| Log Ingestion | 50 GB | $0.57/GB | $28.50 |
| Log Storage | 150 GB | $0.033/GB | $4.95 |
| Metrics (Custom) | 50 metrics | $0.30/metric | $15.00 |
| Dashboard | 1 dashboard | $3.00/dashboard | $3.00 |
| Alarms | 10 alarms | $0.10/alarm | $1.00 |
| **CloudWatch Subtotal** | | | **$52.45** |

#### Calculation Details

**Log Volume:**
- Glue job logs: ~1 GB/day
- Audit logs: ~0.5 GB/day
- Total: 1.5 GB/day × 30 = 45 GB (rounded to 50 GB)

**Storage:**
- 90-day retention: ~150 GB average

### VPC Endpoints

| Component | Units | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| Interface Endpoints | 4 endpoints | $0.011/hr | $31.68 |
| Data Processing | 500 GB | $0.01/GB | $5.00 |
| Gateway Endpoints (S3) | 1 endpoint | Free | $0.00 |
| **VPC Subtotal** | | | **$36.68** |

#### Endpoints Required

1. **com.amazonaws.eu-central-2.glue** - Interface endpoint
2. **com.amazonaws.eu-central-2.logs** - Interface endpoint
3. **com.amazonaws.eu-central-2.kms** - Interface endpoint
4. **com.amazonaws.eu-central-2.secretsmanager** - Interface endpoint
5. **com.amazonaws.eu-central-2.s3** - Gateway endpoint (free)

### AWS Lambda (Supporting Functions)

| Component | Units | Unit Price | Monthly Cost |
|-----------|-------|------------|--------------|
| Invocations | 100K | $0.20/1M | $0.02 |
| Duration (128MB) | 50K GB-seconds | $0.0000166667/GB-s | $0.83 |
| **Lambda Subtotal** | | | **$0.85** |

## Total Monthly Cost Summary

| Service | Monthly Cost |
|---------|--------------|
| AWS Glue | $268.40 |
| Amazon S3 | $118.40 |
| AWS KMS | $61.00 |
| Amazon CloudWatch | $52.45 |
| VPC Endpoints | $36.68 |
| AWS Lambda | $0.85 |
| **Total** | **$537.78** |

## Annual Cost Projection

| Scenario | Monthly | Annual |
|----------|---------|--------|
| Base (as calculated) | $537.78 | $6,453.36 |
| +20% buffer | $645.34 | $7,744.03 |
| High volume (2x) | $985.56 | $11,826.72 |

## Cost Optimization Recommendations

### 1. Glue Job Optimization

**Current**: 10 DPUs for 1 hour
**Optimized**: Auto-scaling with 2-20 DPU range

- **Potential Savings**: 30-40% on DPU costs
- **Implementation**: Enable Glue auto-scaling feature

### 2. S3 Lifecycle Policies

**Recommendation**:
- Move data > 30 days to S3 Intelligent-Tiering
- Move data > 90 days to S3 Glacier
- Delete raw data after 365 days

**Potential Savings**: 60-70% on archive storage

### 3. KMS Request Reduction

**Recommendation**:
- Enable S3 bucket keys (reduces KMS calls by 99%)
- Implement client-side caching for Glue jobs

**Potential Savings**: Up to $55/month on KMS

### 4. CloudWatch Optimization

**Recommendation**:
- Use Log Insights instead of exporting to S3
- Implement log sampling for verbose debug logs
- Archive logs > 30 days to S3

**Potential Savings**: 20-30% on logging costs

## Cost by Environment

| Environment | Multiplier | Monthly Cost |
|-------------|------------|--------------|
| Development | 0.2x | $107.56 |
| Staging | 0.3x | $161.33 |
| Production | 1.0x | $537.78 |
| **Total (all environments)** | | **$806.67** |

## Break-Even Analysis

### vs. On-Premises Solution

**On-Premises Equivalent:**
- Servers: $2,000/month (hardware amortization)
- Storage: $500/month
- Network: $300/month
- Operations: $3,000/month (staff time)
- **Total**: $5,800/month

**AWS Solution**: $537.78/month

**Savings**: $5,262/month (90.7% reduction)

### vs. Alternative Cloud Solutions

| Provider | Equivalent Service | Monthly Cost |
|----------|-------------------|--------------|
| AWS (this solution) | Glue + DataBrew | $537.78 |
| Azure | Data Factory + Databricks | ~$650.00 |
| GCP | Dataflow + Dataprep | ~$580.00 |

## Cost Monitoring

### Budget Alerts

Set up AWS Budgets with the following thresholds:
- 50% of monthly budget: $268.89
- 80% of monthly budget: $430.22
- 100% of monthly budget: $537.78
- 120% anomaly detection: $645.34

### Cost Allocation Tags

Apply these tags to all resources for cost tracking:

```
Project: secure-ml-transformation
Environment: dev|staging|prod
CostCenter: data-engineering
Owner: ml-platform-team
```

## Notes

1. Prices are based on AWS pricing as of January 2024 for eu-central-2 region
2. Actual costs may vary based on usage patterns
3. Reserved capacity options available for predictable workloads
4. Free tier benefits not included in calculations
5. Data transfer costs within VPC are not included (minimal impact)
