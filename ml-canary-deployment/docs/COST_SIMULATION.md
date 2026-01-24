# ML Canary Deployment - Cost Simulation

## Executive Summary

This document provides cost estimates for operating the ML Canary Deployment system serving 50 million daily active users with real-time content recommendations.

**Estimated Monthly Cost: $15,000 - $45,000** (depending on traffic patterns and instance sizing)

## Cost Breakdown

### 1. Amazon SageMaker (Primary Cost Driver)

#### Endpoint Instances
| Configuration | Instance Type | Count | Hours/Month | Rate/Hour | Monthly Cost |
|---------------|---------------|-------|-------------|-----------|--------------|
| Base (Production) | ml.m5.xlarge | 2 | 730 | $0.23 | $335.80 |
| Peak Scaling | ml.m5.xlarge | +8 | 180 | $0.23 | $331.20 |
| Canary (During Deploy) | ml.m5.xlarge | 2 | 100 | $0.23 | $46.00 |
| **Subtotal** | | | | | **$713.00** |

#### With GPU for ML Models (Optional)
| Configuration | Instance Type | Count | Hours/Month | Rate/Hour | Monthly Cost |
|---------------|---------------|-------|-------------|-----------|--------------|
| Base | ml.g4dn.xlarge | 2 | 730 | $0.736 | $1,074.56 |
| Peak Scaling | ml.g4dn.xlarge | +6 | 180 | $0.736 | $795.07 |
| **Subtotal (GPU)** | | | | | **$1,869.63** |

### 2. AWS Lambda

| Function | Invocations/Month | Avg Duration | Memory | Cost |
|----------|-------------------|--------------|--------|------|
| API Handler | 1,500,000,000 | 50ms | 512MB | $6,250.00 |
| Deployment Handler | 1,000 | 5000ms | 512MB | $0.04 |
| Monitoring Handler | 44,640 | 200ms | 512MB | $3.72 |
| Traffic Shift Handler | 5,000 | 100ms | 512MB | $0.21 |
| Rollback Handler | 500 | 100ms | 512MB | $0.02 |
| **Subtotal** | | | | **$6,253.99** |

Note: 50M DAU × 30 requests/day = 1.5B requests/month

### 3. Amazon API Gateway

| Metric | Volume | Rate | Monthly Cost |
|--------|--------|------|--------------|
| REST API Requests | 1,500,000,000 | $3.50/million | $5,250.00 |
| Data Transfer (10KB avg) | 15 TB | $0.09/GB | $1,350.00 |
| **Subtotal** | | | **$6,600.00** |

### 4. Amazon DynamoDB

| Table | Read Units | Write Units | Storage | Monthly Cost |
|-------|------------|-------------|---------|--------------|
| Deployments | 100 | 10 | 1 GB | $25.75 |
| Metrics | 1,000 | 500 | 50 GB | $537.50 |
| Events | 100 | 100 | 10 GB | $100.00 |
| **Subtotal** | | | | **$663.25** |

### 5. Amazon S3

| Bucket | Storage | Requests | Monthly Cost |
|--------|---------|----------|--------------|
| Model Artifacts | 100 GB | 10,000 | $2.30 |
| Inference Logs | 500 GB | 100,000 | $12.00 |
| **Subtotal** | | | **$14.30** |

### 6. Amazon CloudWatch

| Metric | Volume | Rate | Monthly Cost |
|--------|--------|------|--------------|
| Custom Metrics | 50 | $0.30/metric | $15.00 |
| Logs Ingestion | 100 GB | $0.50/GB | $50.00 |
| Logs Storage | 100 GB | $0.03/GB | $3.00 |
| Dashboard | 3 | $3.00/dashboard | $9.00 |
| Alarms | 10 | $0.10/alarm | $1.00 |
| **Subtotal** | | | **$78.00** |

### 7. Amazon SNS

| Metric | Volume | Rate | Monthly Cost |
|--------|--------|------|--------------|
| Notifications | 10,000 | $0.50/million | $0.01 |
| Email Deliveries | 5,000 | $0 (first 1000) | $0.00 |
| **Subtotal** | | | **$0.01** |

## Total Monthly Cost Summary

| Component | Cost (Standard) | Cost (GPU) |
|-----------|-----------------|------------|
| SageMaker Endpoints | $713.00 | $1,869.63 |
| Lambda Functions | $6,253.99 | $6,253.99 |
| API Gateway | $6,600.00 | $6,600.00 |
| DynamoDB | $663.25 | $663.25 |
| S3 | $14.30 | $14.30 |
| CloudWatch | $78.00 | $78.00 |
| SNS | $0.01 | $0.01 |
| **Total** | **$14,322.55** | **$15,479.18** |

## Cost Optimization Strategies

### 1. SageMaker Savings Plans
- **Commitment**: 1-year or 3-year
- **Savings**: Up to 64% on compute costs
- **Recommended for**: Predictable baseline workload

| Plan Type | 1-Year Savings | 3-Year Savings |
|-----------|----------------|----------------|
| ml.m5.xlarge | 33% | 56% |
| ml.g4dn.xlarge | 40% | 64% |

### 2. API Gateway Caching
- Enable caching for repeated requests
- Cache TTL: 300 seconds
- Estimated savings: 30-50% on API costs

### 3. Lambda Provisioned Concurrency
- For predictable high-throughput
- Reduces cold start latency
- Consider for inference handler

### 4. DynamoDB On-Demand vs Provisioned
- On-demand: Better for variable traffic
- Provisioned: Better for predictable traffic
- Consider reserved capacity for 30% savings

### 5. Right-Sizing Instances
| Traffic Level | Recommended Instance | Reason |
|---------------|---------------------|--------|
| < 100 RPS | ml.t3.medium | Cost-effective for low traffic |
| 100-500 RPS | ml.m5.large | Balanced compute/memory |
| 500-2000 RPS | ml.m5.xlarge | Recommended production |
| > 2000 RPS | ml.m5.2xlarge | High throughput |

## Scaling Scenarios

### Scenario 1: Baseline (50M DAU, 30 req/user/day)
- Requests: 1.5B/month
- Peak RPS: ~3,000
- Estimated Cost: **$14,000-16,000/month**

### Scenario 2: Growth (100M DAU)
- Requests: 3B/month
- Peak RPS: ~6,000
- Estimated Cost: **$28,000-35,000/month**

### Scenario 3: Promotional Event (2x traffic)
- Requests: 3B/month (temporary)
- Peak RPS: ~6,000
- Additional Cost: **$10,000-15,000** (for event duration)

## Cost During Canary Deployment

| Phase | Duration | Additional Cost |
|-------|----------|-----------------|
| Initial (10% canary) | 1 hour | ~$0.50 |
| Ramp-up (10-50%) | 4 hours | ~$2.00 |
| Full canary (50-100%) | 4 hours | ~$2.00 |
| Complete | - | Normal operation |
| **Total per deployment** | ~10 hours | **~$4.50** |

## Monitoring Costs

CloudWatch costs scale with:
- Number of metrics published
- Log volume
- Dashboard complexity

Recommendations:
- Use metric filters instead of custom metrics
- Set appropriate log retention (14 days recommended)
- Archive logs to S3 for long-term storage

## Free Tier Considerations

| Service | Free Tier | Notes |
|---------|-----------|-------|
| Lambda | 1M requests/month | Exceeded in production |
| DynamoDB | 25 RCU/WCU | Exceeded in production |
| CloudWatch | 10 metrics | Exceeded in production |
| S3 | 5 GB | Exceeded in production |

## Cost Alerts

Set up AWS Budgets:
1. Monthly budget alert at 80%
2. Daily anomaly detection
3. Service-specific budgets for SageMaker and Lambda
