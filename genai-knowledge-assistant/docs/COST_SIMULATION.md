# Cost Simulation - GenAI Knowledge Assistant

## Overview

This document provides cost estimates for running the GenAI Knowledge Assistant at various scales. Costs are based on AWS pricing for the `eu-central-2` region as of January 2025.

## Service Pricing

### Amazon Bedrock

| Model | Input Tokens | Output Tokens |
|-------|--------------|---------------|
| Claude 3.5 Sonnet | $3.00 / 1M tokens | $15.00 / 1M tokens |
| Claude 3 Haiku | $0.25 / 1M tokens | $1.25 / 1M tokens |
| Titan Embeddings V2 | $0.02 / 1M tokens | - |

### Amazon Bedrock Knowledge Bases
- No additional cost beyond underlying services
- S3 storage for documents
- OpenSearch Serverless for vectors

### OpenSearch Serverless

| Component | Price |
|-----------|-------|
| Indexing OCU | $0.24/hr (~$175/month) |
| Search OCU | $0.24/hr (~$175/month) |
| Storage | $0.024/GB/month |

**Minimum**: 2 OCUs (1 indexing + 1 search) = ~$350/month

### AWS Lambda

| Metric | Price |
|--------|-------|
| Requests | $0.20 / 1M requests |
| Duration | $0.0000166667 / GB-second |
| Free Tier | 1M requests, 400,000 GB-seconds |

### API Gateway

| Metric | Price |
|--------|-------|
| REST API Requests | $3.50 / 1M requests |
| Data Transfer | $0.09 / GB |

### DynamoDB (On-Demand)

| Operation | Price |
|-----------|-------|
| Write | $1.25 / 1M WRU |
| Read | $0.25 / 1M RRU |
| Storage | $0.25 / GB/month |

### S3

| Metric | Price |
|--------|-------|
| Storage | $0.023 / GB/month |
| GET Requests | $0.0004 / 1K requests |
| PUT Requests | $0.005 / 1K requests |

## Cost Scenarios

### Scenario 1: Development / POC

**Usage Profile:**
- 100 queries/day
- 50 documents (100MB total)
- 1 developer

**Monthly Costs:**

| Service | Calculation | Cost |
|---------|-------------|------|
| Bedrock Claude | 3K queries × 2K tokens × $3/1M | $18.00 |
| Bedrock Embeddings | 50 docs × 10K tokens × $0.02/1M | $0.01 |
| OpenSearch Serverless | 2 OCUs minimum | $350.00 |
| Lambda | ~10K invocations (free tier) | $0.00 |
| API Gateway | 3K requests | $0.01 |
| DynamoDB | Minimal (free tier) | $0.00 |
| S3 | 100MB | $0.01 |
| **Total** | | **~$370/month** |

**Note**: OpenSearch Serverless dominates costs at low scale. Consider managed Pinecone or in-memory vector store for POC.

### Scenario 2: Small Business

**Usage Profile:**
- 1,000 queries/day
- 500 documents (1GB total)
- 50 users

**Monthly Costs:**

| Service | Calculation | Cost |
|---------|-------------|------|
| Bedrock Claude | 30K queries × 3K avg tokens × $3-15/1M | $270.00 |
| Bedrock Embeddings | 500 docs × 15K tokens × $0.02/1M | $0.15 |
| OpenSearch Serverless | 2 OCUs | $350.00 |
| Lambda | 100K invocations, 512MB, 5s avg | $25.00 |
| API Gateway | 30K requests | $0.11 |
| DynamoDB | 50K writes, 200K reads | $0.11 |
| S3 | 1GB + requests | $0.10 |
| CloudWatch | Logs and metrics | $15.00 |
| **Total** | | **~$660/month** |

### Scenario 3: Mid-Size Enterprise

**Usage Profile:**
- 10,000 queries/day
- 5,000 documents (10GB total)
- 500 users
- Multiple knowledge bases

**Monthly Costs:**

| Service | Calculation | Cost |
|---------|-------------|------|
| Bedrock Claude | 300K queries × 4K tokens | $3,600.00 |
| Bedrock Embeddings | 5K docs × 20K tokens | $2.00 |
| OpenSearch Serverless | 4 OCUs | $700.00 |
| Lambda | 1M invocations, 1024MB, 8s avg | $200.00 |
| API Gateway | 300K requests | $1.05 |
| DynamoDB | High throughput | $50.00 |
| S3 | 10GB + requests | $1.00 |
| CloudWatch | Enhanced monitoring | $50.00 |
| X-Ray | Tracing | $25.00 |
| **Total** | | **~$4,630/month** |

### Scenario 4: Large Enterprise

**Usage Profile:**
- 100,000 queries/day
- 50,000 documents (100GB total)
- 5,000 users
- High availability requirements

**Monthly Costs:**

| Service | Calculation | Cost |
|---------|-------------|------|
| Bedrock Claude | 3M queries × 4K tokens | $36,000.00 |
| Bedrock Embeddings | 50K docs × 20K tokens | $20.00 |
| OpenSearch Serverless | 8 OCUs (with standby) | $1,400.00 |
| Lambda | 10M invocations, 2048MB | $2,500.00 |
| API Gateway | 3M requests | $10.50 |
| DynamoDB | Reserved capacity | $200.00 |
| S3 | 100GB + lifecycle | $5.00 |
| CloudWatch | Full observability | $200.00 |
| X-Ray | Full tracing | $100.00 |
| WAF | API protection | $30.00 |
| **Total** | | **~$40,500/month** |

## Cost Optimization Strategies

### 1. Model Selection

| Use Case | Recommended Model | Cost Impact |
|----------|-------------------|-------------|
| Simple Q&A | Claude 3 Haiku | -90% on inference |
| Complex reasoning | Claude 3.5 Sonnet | Baseline |
| Summarization | Haiku with prompt caching | -80% |

**Prompt Caching**: For repeated system prompts, use Bedrock's prompt caching to reduce costs by up to 90%.

### 2. Vector Store Alternatives

For lower volume:
- **Pinecone Starter**: Free up to 100K vectors
- **DynamoDB + KNN**: Lower cost, higher latency
- **In-Memory (Lambda)**: For small datasets

### 3. Caching Strategies

```
Query Cache → Semantic Cache → Vector Search → LLM
```

| Cache Layer | Hit Rate | Cost Reduction |
|-------------|----------|----------------|
| Exact match | 10-20% | ~15% |
| Semantic similarity | 30-50% | ~40% |
| Response cache (TTL) | Variable | Depends |

### 4. Request Optimization

| Technique | Savings |
|-----------|---------|
| Batched embeddings | 20-30% |
| Async processing | Latency tolerance |
| Token limit tuning | 10-20% |
| Retrieval threshold | Reduce empty results |

### 5. Infrastructure Optimization

| Optimization | Action | Savings |
|--------------|--------|---------|
| Lambda memory | Right-size to 512MB | 20-40% |
| Reserved capacity | DynamoDB, OpenSearch | 30-50% |
| S3 lifecycle | IA after 90 days | 40% storage |
| Log retention | 30 days non-prod | 50% logs |

## Cost Monitoring

### CloudWatch Metrics to Track

```
# Bedrock usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name InvocationCount \
  --dimensions Name=ModelId,Value=anthropic.claude-3-5-sonnet

# Custom metrics
GenAIKnowledgeAssistant/TokensUsed
GenAIKnowledgeAssistant/QueryCount
GenAIKnowledgeAssistant/DocumentsIngested
```

### Budget Alerts

```hcl
# Terraform - AWS Budgets
resource "aws_budgets_budget" "genai" {
  name         = "genai-assistant-budget"
  budget_type  = "COST"
  limit_amount = "1000"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = ["alerts@example.com"]
  }
}
```

## ROI Considerations

### Value Metrics

| Metric | Measurement |
|--------|-------------|
| Time saved per query | 5-15 minutes |
| Support ticket reduction | 20-40% |
| Employee productivity | 2-4 hours/week |
| Knowledge accessibility | 10x improvement |

### Break-Even Analysis

For a company with:
- 500 employees
- Average salary: $60/hour
- 2 queries/employee/day

**Monthly Value:**
- 500 × 2 × 22 × 10 min saved = 3,667 hours
- Value: 3,667 × $60 = $220,000

**Monthly Cost:** ~$4,630 (Scenario 3)

**ROI:** 47x return

## Appendix: AWS Pricing Calculator Links

- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [OpenSearch Serverless Pricing](https://aws.amazon.com/opensearch-service/pricing/)
- [Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [API Gateway Pricing](https://aws.amazon.com/api-gateway/pricing/)
