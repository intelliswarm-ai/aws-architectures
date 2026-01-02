# AWS SQS Banking Platform - Cost Simulation

This document provides a detailed cost simulation for running the Online Banking Platform with EC2 Auto Scaling for one month. Costs are based on AWS pricing as of January 2025 for the **eu-central-2 (Zurich)** region.

## Table of Contents

1. [Scenario Overview](#scenario-overview)
2. [Cost Summary](#cost-summary)
3. [Detailed Cost Breakdown](#detailed-cost-breakdown)
4. [Cost Optimization Strategies](#cost-optimization-strategies)
5. [Scenario Comparisons](#scenario-comparisons)

---

## Scenario Overview

### Base Scenario: Medium-Volume Banking

| Metric | Value |
|--------|-------|
| **Daily Transactions** | 100,000 |
| **Peak TPS** | 50 transactions/sec |
| **Average TPS** | 2 transactions/sec |
| **EC2 Instances (min/max)** | 2 / 10 |
| **Average Instances** | 3 |
| **Message Size** | 2 KB |
| **Processing Time** | 500 ms/transaction |

---

## Cost Summary

### Monthly Cost Estimate: Base Scenario

| Service | Monthly Cost (USD) | % of Total |
|---------|-------------------|------------|
| Amazon EC2 (t3.medium) | $93.60 | 37.3% |
| Amazon SQS | $1.20 | 0.5% |
| Application Load Balancer | $22.00 | 8.8% |
| Amazon DynamoDB | $25.00 | 10.0% |
| AWS Lambda (Ingestion) | $3.00 | 1.2% |
| Amazon API Gateway | $10.50 | 4.2% |
| CloudWatch | $20.00 | 8.0% |
| Auto Scaling | $0.00 | 0.0% |
| NAT Gateway | $45.00 | 17.9% |
| Other | $30.70 | 12.2% |
| **TOTAL** | **$251.00** | 100% |

```
┌────────────────────────────────────────────────────────────────┐
│                    Monthly Cost Distribution                    │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EC2             ███████████████████░░░░░░░░░░░░░░░░  37.3%    │
│  NAT Gateway     █████████░░░░░░░░░░░░░░░░░░░░░░░░░░  17.9%    │
│  Other           ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  12.2%    │
│  DynamoDB        █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  10.0%    │
│  ALB             ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   8.8%    │
│  CloudWatch      ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   8.0%    │
│  API GW/Lambda   ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   5.4%    │
│  SQS             ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0.5%    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Detailed Cost Breakdown

### 1. Amazon EC2 (Auto Scaling Group)

#### Instance Configuration

| Setting | Value |
|---------|-------|
| Instance type | t3.medium |
| vCPUs | 2 |
| Memory | 4 GB |
| Min instances | 2 |
| Max instances | 10 |
| Avg instances | 3 |

#### Cost Calculation

| Item | Calculation | Cost |
|------|-------------|------|
| On-Demand hours | 3 instances × 720 hours | 2,160 hours |
| On-Demand cost | 2,160 × $0.0416/hour | $89.86 |
| EBS storage | 3 × 20 GB × $0.10/GB | $6.00 |
| **Total** | | **$93.60** |

#### Reserved Instance Savings

| Commitment | Hourly Rate | Monthly | Savings |
|------------|-------------|---------|---------|
| On-Demand | $0.0416 | $93.60 | - |
| 1-year No Upfront | $0.0263 | $56.81 | 39% |
| 1-year All Upfront | $0.0250 | $54.00 | 42% |
| 3-year All Upfront | $0.0163 | $35.21 | 62% |

---

### 2. Amazon SQS

#### Queue Operations

| Queue | Messages/Month | Cost |
|-------|----------------|------|
| Main Queue | 3,000,000 | $1.20 |
| DLQ | 30,000 | $0.01 |
| **Total requests** | 9,000,000 | |

| Item | Calculation | Cost |
|------|-------------|------|
| Standard requests | 9M × $0.40/1M | $3.60 |
| **Free tier** | -1M requests | -$0.40 |
| **After free tier** | | **$1.20** |

> SQS is remarkably cost-effective for message queuing.

---

### 3. Application Load Balancer

| Item | Calculation | Cost |
|------|-------------|------|
| ALB hours | 720 hours × $0.0225 | $16.20 |
| LCU hours | 720 × 1.5 LCU × $0.008 | $8.64 |
| **Total** | | **$22.00** |

#### LCU Calculation

| Dimension | Usage | LCU |
|-----------|-------|-----|
| New connections | 100/sec | 1.0 |
| Active connections | 500 | 0.2 |
| Processed bytes | 5 MB/sec | 0.5 |
| Rule evaluations | 50/sec | 0.5 |
| **Max LCU** | | **1.5** |

---

### 4. Amazon DynamoDB

#### Tables

| Table | Writes/Month | Reads/Month | Storage |
|-------|--------------|-------------|---------|
| Transactions | 3M | 6M | 10 GB |
| Idempotency | 3M | 3M | 2 GB |
| Accounts | 100K | 5M | 1 GB |

#### Costs

| Item | Calculation | Cost |
|------|-------------|------|
| Write requests | 6.1M × $1.25/1M | $7.63 |
| Read requests | 14M × $0.25/1M | $3.50 |
| Storage | 13 GB × $0.25/GB | $3.25 |
| PITR backup | 13 GB × $0.20/GB | $2.60 |
| **Total** | | **$25.00** |

---

### 5. AWS Lambda (Ingestion)

| Item | Calculation | Cost |
|------|-------------|------|
| Invocations | 3M | |
| Duration | 100 ms avg | |
| Memory | 256 MB | |
| GB-seconds | 3M × 0.1s × 0.25 GB | 75,000 GB-s |
| Cost | 75K × $0.0000166667 | $1.25 |
| Requests | 3M × $0.20/1M | $0.60 |
| **Total** | | **$3.00** |

---

### 6. Amazon API Gateway

| Item | Calculation | Cost |
|------|-------------|------|
| REST API requests | 3M × $3.50/1M | $10.50 |
| Data transfer | Included | $0.00 |
| **Total** | | **$10.50** |

---

### 7. NAT Gateway

| Item | Calculation | Cost |
|------|-------------|------|
| NAT Gateway hours | 720 × $0.045 | $32.40 |
| Data processed | 100 GB × $0.045/GB | $4.50 |
| **Total** | | **$45.00** |

> NAT Gateway is a significant fixed cost. Consider alternatives for cost savings.

---

### 8. CloudWatch

| Item | Calculation | Cost |
|------|-------------|------|
| Logs ingestion | 20 GB × $0.50/GB | $10.00 |
| Custom metrics | 30 × $0.30 | $9.00 |
| Alarms | 15 × $0.10 | $1.50 |
| Dashboards | 2 × $3.00 | $6.00 |
| **Free tier offset** | | -$6.50 |
| **Total** | | **$20.00** |

---

## Auto Scaling Behavior

### SQS-Based Scaling

| Metric | Target | Action |
|--------|--------|--------|
| BacklogPerInstance | 100 messages | Scale out |
| BacklogPerInstance | 10 messages | Scale in |
| Cooldown | 300 seconds | Wait between actions |

### Cost During Peak Load

| Instances | Duration | Hourly Cost | Daily Cost |
|-----------|----------|-------------|------------|
| 2 (min) | 20 hours | $0.083 | $1.66 |
| 5 (medium) | 3 hours | $0.208 | $0.62 |
| 10 (max) | 1 hour | $0.416 | $0.42 |
| **Daily Average** | | | **$2.70** |
| **Monthly** | | | **$81.00** |

---

## Cost Optimization Strategies

### 1. EC2 Optimization

| Strategy | Savings | Notes |
|----------|---------|-------|
| Reserved Instances | 40-62% | For min capacity |
| Spot Instances | 70-90% | For burst capacity |
| Right-sizing | Variable | Monitor CPU/memory |
| Graviton (ARM) | 20% | t4g.medium |

#### Hybrid RI + Spot Strategy

| Component | Instances | Cost Model | Monthly |
|-----------|-----------|------------|---------|
| Base capacity | 2 | 1-year RI | $38.00 |
| Burst capacity | 1 avg | Spot | $15.00 |
| **Total** | 3 avg | | **$53.00** |

Savings: **$40/month (43%)**

### 2. NAT Gateway Alternatives

| Option | Cost | Trade-off |
|--------|------|-----------|
| NAT Gateway | $45/month | Fully managed |
| NAT Instance | $15/month | Self-managed, less HA |
| VPC Endpoints | $7/endpoint | For specific services |
| Public subnets | $0 | Security considerations |

### 3. Serverless Alternative

For lower volumes, consider full serverless:

| Service | EC2-Based | Serverless |
|---------|-----------|------------|
| Compute | $93 (EC2) | $15 (Lambda) |
| Queue | $1 (SQS) | $1 (SQS) |
| API | $10 (API GW) | $10 (API GW) |
| **Total** | $251 | $80 |

> Serverless is cheaper below ~50,000 transactions/day.

---

## Scenario Comparisons

| Scenario | Daily TXN | Instances | Monthly Cost |
|----------|-----------|-----------|--------------|
| **Small** | 10,000 | 1-2 | $120-150 |
| **Medium** (Base) | 100,000 | 2-5 | $230-280 |
| **Large** | 500,000 | 5-15 | $600-800 |
| **Enterprise** | 2,000,000 | 20-50 | $2,500-3,500 |

---

## Cost Per Transaction

| Volume | Infrastructure | Cost/TXN |
|--------|----------------|----------|
| 10,000/day | $150 | $0.0050 |
| 100,000/day | $251 | $0.00084 |
| 500,000/day | $700 | $0.00047 |
| 2,000,000/day | $3,000 | $0.00050 |

> Economies of scale flatten around 500K transactions/day.

---

## Annual Cost Projection

| Quarter | Daily TXN | Monthly Cost | Quarterly |
|---------|-----------|--------------|-----------|
| Q1 | 100K | $251 | $753 |
| Q2 | 150K | $320 | $960 |
| Q3 | 200K | $400 | $1,200 |
| Q4 | 250K | $480 | $1,440 |
| **Annual** | | | **$4,353** |

### With Reserved Instances

| Component | On-Demand | With RI | Savings |
|-----------|-----------|---------|---------|
| EC2 | $1,200 | $720 | $480 |
| Other | $3,153 | $3,153 | $0 |
| **Annual** | $4,353 | $3,873 | **$480** |

---

## High Availability Costs

### Multi-AZ Deployment

| Component | Single-AZ | Multi-AZ | Difference |
|-----------|-----------|----------|------------|
| EC2 | $93 | $93 | $0 (auto-distributed) |
| ALB | $22 | $22 | $0 (multi-AZ default) |
| NAT Gateway | $45 | $90 | +$45 |
| RDS (if used) | - | +50% | Variable |
| **Total** | $251 | $296 | **+$45** |

---

## Recommendations

1. **Use Reserved Instances** for minimum capacity (40% savings)
2. **Add Spot Instances** for burst capacity (70% savings on burst)
3. **Evaluate NAT Gateway** - Consider VPC endpoints for S3/DynamoDB
4. **Right-size EC2** - Monitor and adjust instance types
5. **Consider serverless** for volumes under 50K transactions/day
6. **Enable SQS long polling** - Reduces empty receives
7. **Set appropriate visibility timeout** - Avoid duplicate processing
