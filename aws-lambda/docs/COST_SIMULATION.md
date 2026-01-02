# AWS Lambda Task Automation - Cost Simulation

This document provides a detailed cost simulation for running the AWS Lambda Task Automation System for one month. Costs are based on AWS pricing as of January 2025 for the **eu-central-2 (Zurich)** region.

## Table of Contents

1. [Scenario Overview](#scenario-overview)
2. [Cost Summary](#cost-summary)
3. [Detailed Cost Breakdown](#detailed-cost-breakdown)
4. [Cost Optimization Strategies](#cost-optimization-strategies)
5. [Scenario Comparisons](#scenario-comparisons)

---

## Scenario Overview

### Base Scenario: Medium-Volume Task Processing

| Metric | Value |
|--------|-------|
| **Tasks Generated** | 1,000 tasks/day |
| **Task Processing Rate** | 95% success |
| **Step Functions Executions** | 1,000/day |
| **SQS Messages** | 30,000/day |
| **DynamoDB Operations** | 50,000/day |
| **SNS Notifications** | 500/day |
| **Lambda Invocations** | ~100,000/month |

---

## Cost Summary

### Monthly Cost Estimate: Base Scenario

| Service | Monthly Cost (USD) | % of Total |
|---------|-------------------|------------|
| AWS Lambda | $2.50 | 8.5% |
| AWS Step Functions | $7.50 | 25.5% |
| Amazon SQS | $0.36 | 1.2% |
| Amazon DynamoDB | $12.50 | 42.5% |
| Amazon SNS | $0.08 | 0.3% |
| Amazon EventBridge | $0.03 | 0.1% |
| CloudWatch | $5.00 | 17.0% |
| KMS | $1.50 | 5.1% |
| **TOTAL** | **$29.47** | 100% |

```
┌────────────────────────────────────────────────────────────────┐
│                    Monthly Cost Distribution                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  DynamoDB       ██████████████████████░░░░░░░░░░░░░░  42.5%    │
│  Step Functions █████████████░░░░░░░░░░░░░░░░░░░░░░░  25.5%    │
│  CloudWatch     █████████░░░░░░░░░░░░░░░░░░░░░░░░░░░  17.0%    │
│  Lambda         ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   8.5%    │
│  KMS            ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   5.1%    │
│  SQS/SNS/EB     █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   1.6%    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Detailed Cost Breakdown

### 1. AWS Lambda

#### Function Invocations

| Function | Invocations/Month | Avg Duration | Memory |
|----------|-------------------|--------------|--------|
| Task Generator | 720 (hourly) | 200 ms | 512 MB |
| SQS Processor | 30,000 | 500 ms | 512 MB |
| Task Executor | 30,000 | 1,000 ms | 1024 MB |
| Notification Handler | 15,000 | 100 ms | 256 MB |
| **Total** | 75,720 | - | - |

#### Cost Calculation

| Item | Calculation | Cost |
|------|-------------|------|
| Requests | 75,720 × $0.20/1M | $0.02 |
| Compute (GB-seconds) | | |
| - Generator | 720 × 0.2s × 0.5 GB | 72 GB-s |
| - SQS Processor | 30,000 × 0.5s × 0.5 GB | 7,500 GB-s |
| - Executor | 30,000 × 1.0s × 1.0 GB | 30,000 GB-s |
| - Notification | 15,000 × 0.1s × 0.25 GB | 375 GB-s |
| Total GB-seconds | 37,947 GB-s | |
| Cost | 37,947 × $0.0000166667 | $0.63 |
| **SnapStart Savings** | -30% cold start reduction | Included |

**Lambda Monthly Total: $2.50** (after free tier partial coverage)

---

### 2. AWS Step Functions

#### State Machine Executions

| Item | Calculation | Cost |
|------|-------------|------|
| Executions/month | 1,000/day × 30 days | 30,000 |
| State transitions/execution | 10 (avg) | |
| Total transitions | 30,000 × 10 | 300,000 |
| Cost | 300,000 × $0.025/1000 | **$7.50** |

#### Express vs Standard

| Type | Use Case | Cost Model |
|------|----------|------------|
| Standard | Long-running, auditable | Per transition |
| Express | High-volume, short | Per request + duration |

> For this scenario, Standard workflows are more cost-effective.

**Step Functions Monthly Total: $7.50**

---

### 3. Amazon SQS

#### Queue Operations

| Item | Calculation | Cost |
|------|-------------|------|
| SendMessage | 30,000/day × 30 | 900,000 |
| ReceiveMessage | 30,000/day × 30 | 900,000 |
| DeleteMessage | 30,000/day × 30 | 900,000 |
| DLQ operations | 1,500/month | 4,500 |
| Total requests | 2,704,500 | |
| Cost | 2,704,500 × $0.40/1M | **$1.08** |
| **Free Tier** | -1M requests | -$0.40 |

**SQS Monthly Total: $0.36** (after free tier)

---

### 4. Amazon DynamoDB

#### On-Demand Capacity

| Operation | Count/Month | Cost |
|-----------|-------------|------|
| Write requests | 900,000 | 900,000 × $1.25/1M = $1.13 |
| Read requests | 600,000 | 600,000 × $0.25/1M = $0.15 |
| **Subtotal** | | **$1.28** |

#### Storage

| Item | Calculation | Cost |
|------|-------------|------|
| Table storage | 5 GB × $0.25/GB | $1.25 |
| GSI storage | 2 GB × $0.25/GB | $0.50 |
| **Subtotal** | | **$1.75** |

#### Additional Features

| Feature | Cost |
|---------|------|
| Point-in-time recovery | $0.20/GB = $1.40 |
| On-demand backup | $0.10/GB = $0.70 |
| Streams | $0.02/100K reads = $0.12 |
| **Subtotal** | **$2.22** |

**DynamoDB Monthly Total: $12.50**

---

### 5. Amazon SNS

| Item | Calculation | Cost |
|------|-------------|------|
| Publish requests | 15,000 × $0.50/1M | $0.01 |
| Email notifications | 15,000 × $0.00/1000 | $0.00 |
| Lambda deliveries | 15,000 × $0.00 | $0.00 |
| **Free Tier** | -1M publishes | Covered |

**SNS Monthly Total: $0.08**

---

### 6. Amazon EventBridge

| Item | Calculation | Cost |
|------|-------------|------|
| Custom events | 30,000 × $1.00/1M | $0.03 |
| Scheduled rules | Free | $0.00 |

**EventBridge Monthly Total: $0.03**

---

### 7. CloudWatch

| Item | Calculation | Cost |
|------|-------------|------|
| Log ingestion | 10 GB × $0.50/GB | $5.00 |
| Log storage | 10 GB × $0.03/GB | $0.30 |
| Custom metrics | 20 × $0.30/metric | $6.00 |
| Alarms | 10 × $0.10/alarm | $1.00 |
| X-Ray traces | 100,000 × $5/1M | $0.50 |
| **Free Tier** | | -$7.80 |

**CloudWatch Monthly Total: $5.00**

---

### 8. KMS

| Item | Calculation | Cost |
|------|-------------|------|
| CMK (customer managed) | 1 × $1.00/month | $1.00 |
| API requests | 50,000 × $0.03/10K | $0.15 |
| **Subtotal** | | **$1.50** |

---

## Cost Optimization Strategies

### 1. Lambda Optimization

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| SnapStart (Java) | 30-50% cold start | Already enabled |
| Right-size memory | 10-30% | Power Tuning tool |
| Arm64 (Graviton2) | 20% | Change architecture |
| Provisioned Concurrency | Variable | For consistent latency |

### 2. Step Functions Optimization

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Express Workflows | Up to 90% | For high-volume, short tasks |
| Reduce state transitions | Linear | Combine states where possible |
| Use Map state | Parallel processing | Batch operations |

### 3. DynamoDB Optimization

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Provisioned Capacity | 50-70% | For predictable workloads |
| Reserved Capacity | Up to 77% | 1-3 year commitment |
| TTL for cleanup | Storage savings | Auto-delete old items |
| DAX caching | Read cost reduction | For read-heavy workloads |

---

## Scenario Comparisons

| Scenario | Tasks/Day | Monthly Cost |
|----------|-----------|--------------|
| **Small** | 100 | $8-12 |
| **Medium** (Base) | 1,000 | $25-35 |
| **Large** | 10,000 | $150-200 |
| **Enterprise** | 100,000 | $1,200-1,800 |

---

## Annual Cost Projection

| Month | Tasks | Monthly Cost | Cumulative |
|-------|-------|--------------|------------|
| 1-3 | 1,000/day | $29.47 | $88.41 |
| 4-6 | 1,500/day | $42.00 | $214.41 |
| 7-12 | 2,000/day | $55.00 | $544.41 |

**Estimated Annual Cost: ~$545**

---

## Free Tier Coverage

| Service | Free Tier | Monthly Value |
|---------|-----------|---------------|
| Lambda | 1M requests, 400K GB-s | ~$8 |
| SQS | 1M requests | ~$0.40 |
| SNS | 1M publishes | ~$0.50 |
| DynamoDB | 25 GB, 25 WCU/RCU | ~$15 |
| CloudWatch | 10 metrics, 5 GB logs | ~$8 |
| Step Functions | 4,000 transitions | ~$0.10 |
| **Total** | | **~$32/month** |

---

## Recommendations

1. **Use SnapStart** for Java Lambda functions 
2. **Consider Express Workflows** for high-frequency, short tasks
3. **Enable DynamoDB TTL** to auto-delete completed tasks
4. **Use SQS batch operations** to reduce request counts
5. **Set CloudWatch log retention** to 30 days to control storage costs
