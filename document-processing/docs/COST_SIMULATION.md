# AWS ML Document Processing - Cost Simulation

This document provides a detailed cost simulation for running the Intelligent Document Processing Platform for one month. Costs are based on AWS pricing as of January 2025 for the **eu-central-2 (Zurich)** region.

## Table of Contents

1. [Scenario Overview](#scenario-overview)
2. [Cost Summary](#cost-summary)
3. [Detailed Cost Breakdown](#detailed-cost-breakdown)
4. [Cost Optimization Strategies](#cost-optimization-strategies)
5. [Scenario Comparisons](#scenario-comparisons)

---

## Scenario Overview

### Base Scenario: Medium-Volume Document Processing

| Metric | Value |
|--------|-------|
| **Documents Processed** | 5,000/month |
| **Avg Document Pages** | 10 pages |
| **Audio Files (Transcribe)** | 500/month (avg 5 min) |
| **Images Analyzed** | 2,000/month |
| **Bedrock Requests** | 10,000/month |
| **SageMaker Inference** | 5,000/month |

---

## Cost Summary

### Monthly Cost Estimate: Base Scenario

| Service | Monthly Cost (USD) | % of Total |
|---------|-------------------|------------|
| Amazon Textract | $75.00 | 25.8% |
| Amazon Transcribe | $30.00 | 10.3% |
| Amazon Comprehend | $25.00 | 8.6% |
| Amazon Rekognition | $10.00 | 3.4% |
| Amazon Bedrock | $100.00 | 34.4% |
| Amazon SageMaker | $25.00 | 8.6% |
| AWS Lambda | $3.00 | 1.0% |
| AWS Step Functions | $5.00 | 1.7% |
| Amazon S3 | $5.00 | 1.7% |
| CloudWatch | $6.00 | 2.1% |
| Other (KMS, etc.) | $6.00 | 2.1% |
| **TOTAL** | **$290.00** | 100% |

```
┌────────────────────────────────────────────────────────────────┐
│                    Monthly Cost Distribution                    │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Bedrock         █████████████████░░░░░░░░░░░░░░░░░░  34.4%    │
│  Textract        █████████████░░░░░░░░░░░░░░░░░░░░░░  25.8%    │
│  Transcribe      █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  10.3%    │
│  Comprehend      ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   8.6%    │
│  SageMaker       ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   8.6%    │
│  Rekognition     ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   3.4%    │
│  Other           ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   6.6%    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Detailed Cost Breakdown

### 1. Amazon Textract

#### Document Analysis

| Feature | Volume | Unit Price | Cost |
|---------|--------|------------|------|
| Detect Text (pages) | 50,000 | $1.50/1000 | $75.00 |
| Analyze Document (forms) | 10,000 | $50/1000 | $500.00 |
| Analyze Document (tables) | 5,000 | $15/1000 | $75.00 |

**Using Detect Text Only (Base Scenario): $75.00**

> For forms/tables extraction, costs increase significantly.

---

### 2. Amazon Transcribe

| Item | Calculation | Cost |
|------|-------------|------|
| Audio duration | 500 files × 5 min = 2,500 min | |
| Standard transcription | 2,500 × $0.024/min | $60.00 |
| **With batch discount** | 50% for batch jobs | **$30.00** |

---

### 3. Amazon Comprehend

| Feature | Volume | Unit Price | Cost |
|---------|--------|------------|------|
| Sentiment analysis | 50,000 units | $0.0001/unit | $5.00 |
| Entity recognition | 50,000 units | $0.0001/unit | $5.00 |
| Key phrase extraction | 50,000 units | $0.0001/unit | $5.00 |
| Language detection | 50,000 units | $0.0001/unit | $5.00 |
| Custom classification | 5,000 units | $0.0005/unit | $2.50 |
| **Total** | | | **$25.00** |

> 1 unit = 100 characters (3 units per page avg)

---

### 4. Amazon Rekognition

| Feature | Volume | Unit Price | Cost |
|---------|--------|------------|------|
| Label detection | 2,000 images | $1.00/1000 | $2.00 |
| Text in image | 2,000 images | $1.00/1000 | $2.00 |
| Face detection | 1,000 images | $1.00/1000 | $1.00 |
| Content moderation | 2,000 images | $1.00/1000 | $2.00 |
| **Total** | | | **$10.00** |

---

### 5. Amazon Bedrock (Claude 3 Sonnet)

| Operation | Volume | Token Estimate | Cost |
|-----------|--------|----------------|------|
| Document summarization | 5,000 | 2,000 input + 500 output | |
| Q&A extraction | 5,000 | 1,500 input + 300 output | |
| Input tokens | | 17.5M tokens | $52.50 |
| Output tokens | | 4M tokens | $60.00 |
| **Total** | | | **$100.00** |

#### Bedrock Pricing (Claude 3 Sonnet)

| Token Type | Price per 1M tokens |
|------------|---------------------|
| Input | $3.00 |
| Output | $15.00 |

---

### 6. Amazon SageMaker

#### Serverless Inference

| Item | Calculation | Cost |
|------|-------------|------|
| Inference requests | 5,000 | |
| Compute (GB-seconds) | 5,000 × 0.5s × 2 GB | 5,000 GB-s |
| Cost | 5,000 × $0.0000800 | $0.40 |
| Provisioned concurrency | 1 unit × 720 hrs | $20.00 |
| **Total** | | **$25.00** |

---

### 7. AWS Lambda

| Function | Invocations | Duration | Cost |
|----------|-------------|----------|------|
| Document Processor | 5,000 | 2s × 1GB | $0.83 |
| Orchestrator | 15,000 | 0.5s × 512MB | $0.31 |
| Result Handler | 20,000 | 0.2s × 256MB | $0.17 |
| **Total** | | | **$3.00** |

---

### 8. AWS Step Functions

| Item | Calculation | Cost |
|------|-------------|------|
| Workflow executions | 5,000/month | |
| State transitions | 5,000 × 20 states | 100,000 |
| Cost | 100,000 × $0.025/1000 | **$5.00** |

---

### 9. Amazon S3

| Item | Size | Cost |
|------|------|------|
| Document storage | 50 GB | $1.15 |
| Processed results | 10 GB | $0.23 |
| Model artifacts | 5 GB | $0.12 |
| PUT/GET requests | 500,000 | $2.50 |
| **Total** | | **$5.00** |

---

## Cost Optimization Strategies

### 1. Textract Optimization

| Strategy | Savings | Notes |
|----------|---------|-------|
| Use DetectText for simple docs | 70% | vs AnalyzeDocument |
| Batch processing | 10-20% | Lower per-page cost |
| Pre-filter pages | Variable | Skip blank pages |

### 2. Bedrock Optimization

| Strategy | Savings | Notes |
|----------|---------|-------|
| Use Haiku for simple tasks | 90% | $0.25/$1.25 per 1M tokens |
| Prompt caching | 50-80% | Reuse common prefixes |
| Reduce output length | Linear | Shorter summaries |

### 3. SageMaker Optimization

| Strategy | Savings | Notes |
|----------|---------|-------|
| Serverless for low volume | Variable | Pay per request |
| Spot instances for training | 70% | Interruptible |
| Multi-model endpoints | 50%+ | Share infrastructure |

---

## Scenario Comparisons

| Scenario | Documents/Month | Monthly Cost |
|----------|-----------------|--------------|
| **Small** | 500 | $50-80 |
| **Medium** (Base) | 5,000 | $250-350 |
| **Large** | 25,000 | $1,000-1,500 |
| **Enterprise** | 100,000 | $4,000-6,000 |

---

## Cost by Document Type

| Document Type | Services Used | Cost/Doc |
|---------------|---------------|----------|
| Simple PDF (text only) | Textract + Comprehend | $0.02 |
| Scanned document | Textract + Comprehend + Rekognition | $0.05 |
| Audio file | Transcribe + Comprehend + Bedrock | $0.15 |
| Complex document (forms) | Textract (forms) + Bedrock | $0.12 |

---

## Annual Cost Projection

| Quarter | Documents | Quarterly Cost |
|---------|-----------|----------------|
| Q1 | 15,000 | $870 |
| Q2 | 20,000 | $1,160 |
| Q3 | 25,000 | $1,450 |
| Q4 | 30,000 | $1,740 |
| **Annual** | 90,000 | **$5,220** |

---

## Recommendations

1. **Use Claude 3 Haiku** for simple summarization tasks (10x cheaper)
2. **Batch Textract jobs** for cost efficiency
3. **Pre-filter documents** to skip irrelevant pages
4. **Cache common prompts** in Bedrock
5. **Use Comprehend batch APIs** for high-volume analysis
6. **Consider reserved capacity** for predictable workloads
