# AWS Elastic Beanstalk Hybrid Cloud - Cost Simulation

This document provides a detailed cost simulation for running the Hybrid Cloud Enterprise Inventory Management System for one month. Costs are based on AWS pricing as of January 2025 for the **eu-central-2 (Zurich)** region.

## Table of Contents

1. [Scenario Overview](#scenario-overview)
2. [Cost Summary](#cost-summary)
3. [Detailed Cost Breakdown](#detailed-cost-breakdown)
4. [Cost Optimization Strategies](#cost-optimization-strategies)
5. [Scenario Comparisons](#scenario-comparisons)

---

## Scenario Overview

### Base Scenario: Production Environment

| Metric | Value |
|--------|-------|
| **EC2 Instance Type** | t3.medium |
| **Instance Count (Avg)** | 2 (Auto Scaling 2-4) |
| **Connectivity** | VPN Gateway |
| **Database** | On-Premises Oracle (not in AWS) |
| **Monthly API Requests** | 500,000 |
| **Report Generation** | 100 reports/month |
| **Data Transfer (VPN)** | 50 GB/month |
| **S3 Storage** | 10 GB |

---

## Cost Summary

### Monthly Cost Estimate: Base Scenario

| Service | Monthly Cost (USD) | % of Total |
|---------|-------------------|------------|
| Amazon EC2 (Elastic Beanstalk) | $62.00 | 28.3% |
| VPN Gateway | $36.00 | 16.4% |
| NAT Gateway | $45.00 | 20.5% |
| Application Load Balancer | $25.00 | 11.4% |
| Amazon S3 | $3.00 | 1.4% |
| CloudWatch | $15.00 | 6.8% |
| Data Transfer | $8.00 | 3.6% |
| Other | $25.00 | 11.4% |
| **TOTAL** | **$219.00** | 100% |

```
┌────────────────────────────────────────────────────────────────┐
│                    Monthly Cost Distribution                    │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EC2 (Beanstalk)  ██████████████░░░░░░░░░░░░░░░░░░░░  28.3%    │
│  NAT Gateway      ██████████░░░░░░░░░░░░░░░░░░░░░░░░  20.5%    │
│  VPN Gateway      ████████░░░░░░░░░░░░░░░░░░░░░░░░░░  16.4%    │
│  ALB              █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  11.4%    │
│  Other            █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  11.4%    │
│  CloudWatch       ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   6.8%    │
│  Data Transfer    ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   3.6%    │
│  S3               ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   1.4%    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Detailed Cost Breakdown

### 1. Amazon EC2 (Elastic Beanstalk)

#### Instance Configuration

| Setting | Development | Production |
|---------|-------------|------------|
| Instance type | t3.small | t3.medium |
| Min instances | 1 | 2 |
| Max instances | 2 | 4 |
| Avg instances | 1 | 2 |

#### Production Costs

| Item | Calculation | Cost |
|------|-------------|------|
| Instance hours | 2 × 720 hours | 1,440 hours |
| On-Demand cost | 1,440 × $0.0416/hour | $59.90 |
| EBS storage | 2 × 8 GB × $0.10/GB | $1.60 |
| **Total** | | **$62.00** |

#### Reserved Instance Savings

| Commitment | Hourly Rate | Monthly (2 inst) | Savings |
|------------|-------------|------------------|---------|
| On-Demand | $0.0416 | $62.00 | - |
| 1-year No Upfront | $0.0263 | $37.87 | 39% |
| 1-year All Upfront | $0.0250 | $36.00 | 42% |
| 3-year All Upfront | $0.0163 | $23.47 | 62% |

---

### 2. VPN Gateway

| Item | Calculation | Cost |
|------|-------------|------|
| VPN Gateway hours | 720 hours × $0.05/hour | $36.00 |
| VPN connection | 1 connection × $0.05/hour × 720 | Included |
| **Total** | | **$36.00** |

#### Data Transfer via VPN

| Item | Calculation | Cost |
|------|-------------|------|
| Data out to on-premises | 50 GB × $0.09/GB | $4.50 |
| Data in from on-premises | 50 GB × $0.00/GB | $0.00 |
| **Total** | | **$4.50** |

> VPN latency: 20-50ms typical

---

### 3. Direct Connect Alternative (Production)

For lower latency and consistent bandwidth:

| Item | Calculation | Cost |
|------|-------------|------|
| Dedicated connection (1 Gbps) | Port fee | $220.00 |
| Data transfer (outbound) | 50 GB × $0.02/GB | $1.00 |
| Partner fees | Variable | $100-500 |
| **Total** | | **$321-721** |

#### VPN vs Direct Connect

| Aspect | VPN | Direct Connect |
|--------|-----|----------------|
| Monthly cost | $41 | $320+ |
| Latency | 20-50ms | 1-5ms |
| Bandwidth | Variable | Guaranteed |
| Setup time | Hours | Weeks-Months |
| Best for | Dev/Test | Production |

---

### 4. NAT Gateway

| Item | Calculation | Cost |
|------|-------------|------|
| NAT Gateway hours | 720 hours × $0.045/hour | $32.40 |
| Data processed | 100 GB × $0.045/GB | $4.50 |
| **Total** | | **$45.00** |

> NAT Gateway is a significant fixed cost. Consider NAT Instance for dev/test.

---

### 5. Application Load Balancer

| Item | Calculation | Cost |
|------|-------------|------|
| ALB hours | 720 hours × $0.0225/hour | $16.20 |
| LCU hours | 720 × 1.2 LCU × $0.008 | $6.91 |
| **Total** | | **$25.00** |

#### LCU Calculation

| Dimension | Usage | LCU |
|-----------|-------|-----|
| New connections | 50/sec | 0.5 |
| Active connections | 300 | 0.1 |
| Processed bytes | 3 MB/sec | 0.3 |
| Rule evaluations | 30/sec | 0.3 |
| **Max LCU** | | **1.2** |

---

### 6. Amazon S3

#### Reports Bucket

| Item | Calculation | Cost |
|------|-------------|------|
| Standard storage | 10 GB × $0.023/GB | $0.23 |
| IA storage (90+ days) | 20 GB × $0.0125/GB | $0.25 |
| Glacier (365+ days) | 50 GB × $0.004/GB | $0.20 |
| PUT requests | 1,000 × $0.005/1K | $0.01 |
| GET requests | 5,000 × $0.0004/1K | $0.00 |
| **Total** | | **$3.00** |

#### Lifecycle Policy

| Age | Storage Class | Cost/GB |
|-----|---------------|---------|
| 0-90 days | Standard | $0.023 |
| 90-365 days | Standard-IA | $0.0125 |
| 365+ days | Glacier | $0.004 |
| 7 years | Expire | - |

---

### 7. CloudWatch

| Item | Calculation | Cost |
|------|-------------|------|
| Log ingestion | 15 GB × $0.50/GB | $7.50 |
| Log storage | 15 GB × $0.03/GB | $0.45 |
| Custom metrics | 20 × $0.30 | $6.00 |
| Alarms | 10 × $0.10 | $1.00 |
| Dashboard | 1 × $3.00 | $3.00 |
| **Free tier offset** | | -$3.95 |
| **Total** | | **$15.00** |

---

### 8. Other Costs

| Item | Cost | Notes |
|------|------|-------|
| Elastic Beanstalk | $0.00 | No additional charge |
| KMS (S3 encryption) | $1.00 | 1 CMK |
| KMS requests | $0.50 | API calls |
| Secrets Manager | $2.00 | DB credentials |
| ACM (SSL cert) | $0.00 | Free for ALB |
| Route 53 | $0.50 | Hosted zone |
| VPC Endpoints | $0.00 | Not used |
| **Subtotal** | **$25.00** | With buffer |

---

## Environment Comparison

### Cost by Environment

| Resource | Development | Staging | Production |
|----------|-------------|---------|------------|
| EC2 (t3.small/medium) | $15 | $32 | $62 |
| VPN Gateway | $36 | $36 | $36 |
| NAT Gateway | $0 (NAT Instance) | $45 | $45 |
| ALB | $18 | $22 | $25 |
| S3 | $1 | $2 | $3 |
| CloudWatch | $5 | $10 | $15 |
| Other | $10 | $15 | $25 |
| **Total** | **$85** | **$162** | **$219** |

### Development Cost Optimization

| Optimization | Savings | Notes |
|--------------|---------|-------|
| NAT Instance (t3.micro) | $40/month | vs NAT Gateway |
| t3.small (1 instance) | $30/month | vs t3.medium (2) |
| Single AZ | $0 | Reduced HA |
| Shutdown nights/weekends | 60% | ~$50/month |

**Optimized Dev Cost: ~$35/month**

---

## Hybrid Connectivity Deep Dive

### VPN Performance by Database Operation

| Operation | Latency Impact | Mitigation |
|-----------|----------------|------------|
| Simple query | +20-50ms | Acceptable |
| Complex query | +100-200ms | Connection pooling |
| Bulk insert | +500ms-2s | Batch operations |
| Report generation | +2-5s | Async processing |

### Connection Pool Optimization

| Setting | VPN | Direct Connect |
|---------|-----|----------------|
| Min connections | 5 | 10 |
| Max connections | 20 | 30 |
| Connection timeout | 30s | 20s |
| Idle timeout | 300s | 180s |
| Max lifetime | 1200s | 900s |

---

## Auto Scaling Cost Impact

### Scaling Patterns

| Pattern | Avg Instances | Peak Instances | Monthly Cost |
|---------|---------------|----------------|--------------|
| Steady | 2.0 | 2 | $62 |
| Business hours | 2.5 | 4 | $78 |
| Peak periods | 3.0 | 4 | $93 |

### Scaling Policy Costs

| Trigger | Scale Out | Scale In | Impact |
|---------|-----------|----------|--------|
| CPU > 70% | +1 | - | +$31/instance |
| CPU < 30% | - | -1 | -$31/instance |
| Requests > 1000/min | +1 | - | +$31/instance |

---

## Cost Optimization Strategies

### 1. EC2 Optimization

| Strategy | Savings | Notes |
|----------|---------|-------|
| Reserved Instances | 40-62% | For baseline capacity |
| Spot Instances | 70-90% | For burst capacity |
| Graviton (t4g) | 20% | ARM-based instances |
| Right-sizing | Variable | Monitor utilization |

#### Hybrid RI + On-Demand Strategy

| Component | Instances | Cost Model | Monthly |
|-----------|-----------|------------|---------|
| Base (min) | 2 | 1-year RI | $36.00 |
| Burst | 0-2 avg 0.5 | On-Demand | $15.00 |
| **Total** | | | **$51.00** |

**Savings: $11/month (18%)**

### 2. NAT Gateway Alternatives

| Option | Monthly Cost | Pros | Cons |
|--------|--------------|------|------|
| NAT Gateway | $45 | Managed, HA | Expensive |
| NAT Instance (t3.micro) | $8 | Cheap | Self-managed |
| VPC Endpoints | $7/endpoint | Per-service | Limited services |
| Public subnets | $0 | Free | Security risk |

**Recommendation**: NAT Instance for dev, NAT Gateway for prod.

### 3. VPN vs Direct Connect Decision

| Factor | Choose VPN | Choose Direct Connect |
|--------|------------|----------------------|
| Budget | < $500/month total | > $500/month total |
| Latency requirement | > 50ms OK | < 10ms required |
| Traffic volume | < 1 TB/month | > 1 TB/month |
| Environment | Dev/Test | Production |

### 4. Elastic Beanstalk Optimization

| Setting | Cost Impact | Recommendation |
|---------|-------------|----------------|
| Enhanced health | +$0/month | Enable (free) |
| Managed updates | +$0/month | Enable (free) |
| Multi-AZ | +100% EC2 | Prod only |
| Spot instances | -60-80% | Dev/Test |

---

## Scenario Comparisons

| Scenario | EC2 | Connectivity | Total/Month |
|----------|-----|--------------|-------------|
| **Dev (minimal)** | 1× t3.micro | VPN | $50-70 |
| **Dev (standard)** | 1× t3.small | VPN | $80-100 |
| **Staging** | 2× t3.small | VPN | $150-180 |
| **Production (VPN)** | 2× t3.medium | VPN | $200-250 |
| **Production (DC)** | 2× t3.medium | Direct Connect | $500-700 |

---

## Multi-Environment Setup

### Total Cost (All Environments)

| Environment | Monthly Cost | Notes |
|-------------|--------------|-------|
| Development | $85 | Shared VPN |
| Staging | $162 | Shared VPN |
| Production | $219 | Dedicated |
| **Total** | **$466** | |

### Shared VPN Savings

| Configuration | Cost | Savings |
|---------------|------|---------|
| 3 separate VPNs | $108 | - |
| 1 shared VPN | $36 | $72/month |

---

## Annual Cost Projection

### With Growth

| Quarter | EC2 Instances | Connectivity | Quarterly |
|---------|---------------|--------------|-----------|
| Q1 | 2 avg | VPN | $657 |
| Q2 | 2.5 avg | VPN | $750 |
| Q3 | 3 avg | VPN | $843 |
| Q4 | 3 avg | Direct Connect | $1,500 |
| **Annual** | | | **$3,750** |

### With Reserved Instances

| Component | On-Demand | Reserved | Savings |
|-----------|-----------|----------|---------|
| EC2 (annual) | $744 | $432 | $312 |
| NAT Gateway | $540 | $540 | $0 |
| Other | $2,466 | $2,466 | $0 |
| **Annual** | $3,750 | $3,438 | **$312** |

---

## On-Premises Costs (Not Included)

These costs are separate from AWS:

| Resource | Estimated Cost | Notes |
|----------|----------------|-------|
| Oracle Database License | $17,500/CPU/year | Enterprise Edition |
| Oracle Support | $3,850/CPU/year | 22% of license |
| Server hardware | $500-1000/month | Depreciation |
| Datacenter | $200-500/month | Power, cooling, space |
| Network equipment | $100-200/month | Router, firewall |
| **Total On-Prem** | **$2,000-3,000/month** | |

### Full Hybrid TCO

| Component | Monthly Cost |
|-----------|--------------|
| AWS infrastructure | $219 |
| On-premises (est.) | $2,500 |
| **Total TCO** | **$2,719** |

---

## Migration Path Costs

### Phase 1: Hybrid (Current)

| AWS Services | Monthly |
|--------------|---------|
| Elastic Beanstalk + VPN | $219 |

### Phase 2: Database Migration

| Additional AWS Services | Monthly |
|-------------------------|---------|
| Amazon RDS Oracle | $800+ |
| Data Migration Service | $50 (one-time) |
| **Total** | **$1,019** |

### Phase 3: Full Cloud

| AWS Services | Monthly |
|--------------|---------|
| Elastic Beanstalk | $90 |
| Amazon Aurora PostgreSQL | $300 |
| No VPN needed | -$36 |
| **Total** | **$354** |

---

## Free Tier Coverage

| Service | Free Tier | Monthly Value |
|---------|-----------|---------------|
| EC2 | 750 hours t2/t3.micro | ~$8 |
| S3 | 5 GB storage | ~$0.12 |
| CloudWatch | 10 metrics, 5 GB logs | ~$5 |
| Elastic Beanstalk | No charge | $0 |
| **Total** | | **~$13/month** |

---

## Recommendations

1. **Use NAT Instance for dev** - Save $37/month vs NAT Gateway
2. **Reserve baseline EC2** - 40% savings on minimum instances
3. **Share VPN across environments** - Save $72/month
4. **Enable connection pooling** - Reduce VPN latency impact
5. **Consider Direct Connect for production** - If latency is critical
6. **Implement caching** - Reduce database round-trips over VPN
7. **Use Graviton instances** - 20% cheaper, better performance
8. **Schedule dev environment shutdown** - 60% savings on dev

