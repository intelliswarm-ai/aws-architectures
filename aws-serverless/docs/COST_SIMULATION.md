# AWS Serverless Multi-Tenant SaaS - Cost Simulation

This document provides a detailed cost simulation for running the Multi-Tenant SaaS Platform (intelliswarm.ai) for one month. Costs are based on AWS pricing as of January 2025 for the **eu-central-2 (Zurich)** region.

## Table of Contents

1. [Scenario Overview](#scenario-overview)
2. [Cost Summary](#cost-summary)
3. [Detailed Cost Breakdown](#detailed-cost-breakdown)
4. [Cost Optimization Strategies](#cost-optimization-strategies)
5. [Scenario Comparisons](#scenario-comparisons)

---

## Scenario Overview

### Base Scenario: Growth-Stage SaaS

| Metric | Value |
|--------|-------|
| **Active Tenants** | 50 companies |
| **Monthly Active Users (MAU)** | 500 users |
| **API Requests** | 2,000,000/month |
| **Email Processing** | 100,000 emails/month |
| **Bedrock AI Requests** | 50,000/month |
| **Data Storage** | 100 GB |

---

## Cost Summary

### Monthly Cost Estimate: Base Scenario

| Service | Monthly Cost (USD) | % of Total |
|---------|-------------------|------------|
| Amazon Cognito | $27.50 | 4.9% |
| Amazon Bedrock | $250.00 | 44.3% |
| AWS Lambda | $15.00 | 2.7% |
| Amazon API Gateway | $7.00 | 1.2% |
| Amazon DynamoDB | $35.00 | 6.2% |
| AWS WAF | $11.00 | 1.9% |
| AWS KMS | $15.00 | 2.7% |
| AWS Secrets Manager | $12.00 | 2.1% |
| Amazon VPC (Endpoints) | $75.00 | 13.3% |
| CloudWatch | $20.00 | 3.5% |
| CloudTrail | $5.00 | 0.9% |
| AWS Config | $10.00 | 1.8% |
| S3 | $8.00 | 1.4% |
| Other | $74.50 | 13.2% |
| **TOTAL** | **$565.00** | 100% |

```
┌────────────────────────────────────────────────────────────────┐
│                    Monthly Cost Distribution                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Bedrock         ██████████████████████░░░░░░░░░░░░░  44.3%    │
│  VPC Endpoints   ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  13.3%    │
│  DynamoDB        ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   6.2%    │
│  Cognito         ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   4.9%    │
│  CloudWatch      ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   3.5%    │
│  Lambda/KMS      ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   5.4%    │
│  Other           ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  22.4%    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Detailed Cost Breakdown

### 1. Amazon Cognito

| Item | Calculation | Cost |
|------|-------------|------|
| MAU (first 50K) | 500 × $0.0055 | $2.75 |
| Advanced Security | 500 × $0.050 | $25.00 |
| SMS MFA (optional) | 100 × $0.01 | $1.00 |
| **Total** | | **$27.50** |

> Advanced Security includes compromised credential detection and adaptive authentication.

---

### 2. Amazon Bedrock (Claude 3 Sonnet)

| Operation | Volume | Tokens | Cost |
|-----------|--------|--------|------|
| Email analysis | 100,000 | 1,500 in + 300 out | |
| Intent detection | 50,000 | 500 in + 100 out | |
| Summarization | 25,000 | 2,000 in + 500 out | |
| **Input tokens** | | 200M | $600.00 |
| **Output tokens** | | 50M | $750.00 |
| **With caching (80%)** | | | **$250.00** |

> Prompt caching reduces costs by ~80% for repetitive patterns.

---

### 3. AWS Lambda

| Function | Invocations | Duration | Memory | Cost |
|----------|-------------|----------|--------|------|
| API Handlers | 2,000,000 | 100 ms | 512 MB | $5.00 |
| Email Processor | 100,000 | 500 ms | 1024 MB | $4.17 |
| Auth Lambda | 500,000 | 50 ms | 256 MB | $0.52 |
| Background Jobs | 50,000 | 2s | 512 MB | $4.17 |
| **Total** | | | | **$15.00** |

---

### 4. Amazon API Gateway

| Item | Calculation | Cost |
|------|-------------|------|
| REST API requests | 2,000,000 × $3.50/1M | $7.00 |
| Data transfer | Included | $0.00 |
| **Total** | | **$7.00** |

---

### 5. Amazon DynamoDB

| Item | Calculation | Cost |
|------|-------------|------|
| Write requests | 5M × $1.25/1M | $6.25 |
| Read requests | 20M × $0.25/1M | $5.00 |
| Storage | 50 GB × $0.25/GB | $12.50 |
| Global tables (DR) | 50 GB × $0.25/GB | $12.50 |
| Streams | 10M × $0.02/100K | $2.00 |
| **Total** | | **$35.00** |

---

### 6. AWS WAF

| Item | Calculation | Cost |
|------|-------------|------|
| Web ACL | 1 × $5.00 | $5.00 |
| Rules | 10 × $1.00 | $10.00 |
| Requests | 2M × $0.60/1M | $1.20 |
| **Total** | | **$11.00** |

---

### 7. AWS KMS

| Item | Calculation | Cost |
|------|-------------|------|
| CMKs | 5 × $1.00 | $5.00 |
| API requests | 2M × $0.03/10K | $6.00 |
| **Total** | | **$15.00** |

---

### 8. AWS Secrets Manager

| Item | Calculation | Cost |
|------|-------------|------|
| Secrets stored | 20 × $0.40 | $8.00 |
| API calls | 100K × $0.05/10K | $0.50 |
| Rotation Lambda | Included in Lambda | $0.00 |
| **Total** | | **$12.00** |

---

### 9. Amazon VPC (Private Endpoints)

| Endpoint | Hours | Cost |
|----------|-------|------|
| S3 Gateway | Free | $0.00 |
| DynamoDB Gateway | Free | $0.00 |
| Secrets Manager | 720 × $0.01 | $7.20 |
| Bedrock | 720 × $0.01 | $7.20 |
| KMS | 720 × $0.01 | $7.20 |
| STS | 720 × $0.01 | $7.20 |
| CloudWatch | 720 × $0.01 | $7.20 |
| **Total (5 Interface Endpoints)** | | **$75.00** |

> VPC Endpoints enable private connectivity but add significant fixed costs.

---

### 10. CloudWatch

| Item | Calculation | Cost |
|------|-------------|------|
| Logs ingestion | 20 GB × $0.50/GB | $10.00 |
| Logs storage | 20 GB × $0.03/GB | $0.60 |
| Custom metrics | 50 × $0.30 | $15.00 |
| Dashboards | 3 × $3.00 | $9.00 |
| Alarms | 20 × $0.10 | $2.00 |
| X-Ray traces | 500K × $5/1M | $2.50 |
| **Free tier offset** | | -$19.10 |
| **Total** | | **$20.00** |

---

### 11. CloudTrail

| Item | Calculation | Cost |
|------|-------------|------|
| Management events | First trail free | $0.00 |
| Data events (S3) | 5M × $0.10/100K | $5.00 |
| Insights | Not enabled | $0.00 |
| **Total** | | **$5.00** |

---

### 12. AWS Config

| Item | Calculation | Cost |
|------|-------------|------|
| Configuration items | 10K × $0.003 | $3.00 |
| Rule evaluations | 50K × $0.001 | $5.00 |
| Conformance packs | 2 × $1.00 | $2.00 |
| **Total** | | **$10.00** |

---

### 13. Amazon S3

| Item | Calculation | Cost |
|------|-------------|------|
| Storage | 100 GB × $0.023/GB | $2.30 |
| PUT requests | 500K × $0.005/1K | $2.50 |
| GET requests | 2M × $0.0004/1K | $0.80 |
| Data transfer | 50 GB × $0.00 (in-region) | $0.00 |
| **Total** | | **$8.00** |

---

## Cost Per Tenant Analysis

### Monthly Cost Per Tenant

| Cost Component | Per Tenant |
|----------------|------------|
| Fixed costs (VPC, WAF, etc.) | $2.00 |
| Variable costs (usage-based) | $9.30 |
| **Total per tenant** | **$11.30** |

### Cost Per User

| MAU Range | Cost/User |
|-----------|-----------|
| 1-100 | $5.65 |
| 101-500 | $1.13 |
| 501-1000 | $0.68 |
| 1000+ | $0.45 |

---

## Cost Optimization Strategies

### 1. VPC Endpoints (Biggest Fixed Cost)

| Strategy | Savings | Notes |
|----------|---------|-------|
| Remove non-essential endpoints | $7-35/month per endpoint | Keep only critical ones |
| Use NAT Gateway instead | Variable | Higher data transfer cost |
| Share endpoints across VPCs | 50%+ | Transit Gateway |

### 2. Bedrock Optimization

| Strategy | Savings | Notes |
|----------|---------|-------|
| Prompt caching | 80% | Already applied |
| Use Haiku for simple tasks | 90% | For classification |
| Batch processing | 50% | Async workflows |

### 3. Multi-Tenant Optimization

| Strategy | Savings | Notes |
|----------|---------|-------|
| Tenant pooling | 30-50% | Shared resources |
| Usage-based pricing | Variable | Pass costs to tenants |
| Tiered features | Variable | Premium vs basic |

---

## Scenario Comparisons

| Scenario | Tenants | MAU | Monthly Cost |
|----------|---------|-----|--------------|
| **Startup** | 10 | 100 | $180-250 |
| **Growth** (Base) | 50 | 500 | $500-650 |
| **Scale** | 200 | 2,000 | $1,800-2,500 |
| **Enterprise** | 500 | 10,000 | $6,000-9,000 |

---

## Break-Even Analysis

### Pricing Model Assumptions

| Tier | Price/User/Month | Features |
|------|------------------|----------|
| Basic | $10 | Core features |
| Pro | $25 | + AI features |
| Enterprise | $50 | + SSO, compliance |

### Break-Even Points

| Cost Level | Users Needed (Basic) | Users Needed (Pro) |
|------------|---------------------|-------------------|
| $565/month | 57 users | 23 users |
| $1,000/month | 100 users | 40 users |
| $2,500/month | 250 users | 100 users |

---

## Annual Cost Projection

| Quarter | Tenants | MAU | Quarterly Cost |
|---------|---------|-----|----------------|
| Q1 | 50 | 500 | $1,695 |
| Q2 | 100 | 1,000 | $2,700 |
| Q3 | 150 | 1,500 | $3,600 |
| Q4 | 200 | 2,000 | $4,500 |
| **Annual** | | | **$12,495** |

---

## Recommendations

1. **Evaluate VPC Endpoints** - Remove if not required for compliance
2. **Implement Bedrock caching** - Already configured, monitor effectiveness
3. **Use Cognito Lite** - If advanced security not needed, save $25/month
4. **Right-size DynamoDB** - Consider provisioned capacity for stable workloads
5. **Consolidate CloudWatch** - Use log groups with shorter retention
6. **Monitor per-tenant costs** - Implement usage tracking for billing
