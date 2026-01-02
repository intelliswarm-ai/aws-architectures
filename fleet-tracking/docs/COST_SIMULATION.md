# AWS Kinesis GPS Tracking - Cost Simulation

This document provides a detailed cost simulation for running the Real-Time GPS Tracking System for one month. Costs are based on AWS pricing as of January 2025 for the **eu-central-2 (Zurich)** region.

## Table of Contents

1. [Scenario Overview](#scenario-overview)
2. [Cost Summary](#cost-summary)
3. [Detailed Cost Breakdown](#detailed-cost-breakdown)
4. [Cost Optimization Strategies](#cost-optimization-strategies)
5. [Scenario Comparisons](#scenario-comparisons)

---

## Scenario Overview

### Base Scenario: Medium Fleet Tracking

| Metric | Value |
|--------|-------|
| **Fleet Size** | 100 trucks |
| **GPS Updates** | Every 5 seconds |
| **Updates/Truck/Day** | 17,280 |
| **Total Updates/Day** | 1,728,000 |
| **Monthly Records** | ~52,000,000 |
| **Geofences** | 50 defined |
| **Alerts/Day** | 500 |

---

## Cost Summary

### Monthly Cost Estimate: Base Scenario

| Service | Monthly Cost (USD) | % of Total |
|---------|-------------------|------------|
| Amazon Kinesis Data Streams | $36.00 | 30.0% |
| AWS Lambda (Consumers) | $25.00 | 20.8% |
| Amazon DynamoDB | $30.00 | 25.0% |
| Amazon S3 | $8.00 | 6.7% |
| Amazon SNS | $0.50 | 0.4% |
| Amazon EventBridge | $0.02 | 0.0% |
| CloudWatch | $15.00 | 12.5% |
| KMS | $3.00 | 2.5% |
| Other | $2.48 | 2.1% |
| **TOTAL** | **$120.00** | 100% |

```
┌────────────────────────────────────────────────────────────────┐
│                    Monthly Cost Distribution                    │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Kinesis         ███████████████░░░░░░░░░░░░░░░░░░░░  30.0%    │
│  DynamoDB        █████████████░░░░░░░░░░░░░░░░░░░░░░  25.0%    │
│  Lambda          ██████████░░░░░░░░░░░░░░░░░░░░░░░░░  20.8%    │
│  CloudWatch      ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  12.5%    │
│  S3              ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   6.7%    │
│  Other           ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   5.0%    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Detailed Cost Breakdown

### 1. Amazon Kinesis Data Streams

#### Shard Configuration

| Metric | Value |
|--------|-------|
| Records/second | 20 (1,728,000 / 86,400) |
| Record size | 500 bytes |
| Throughput | 10 KB/s |
| Shards needed | 2 (1 MB/s capacity each) |

#### Costs

| Item | Calculation | Cost |
|------|-------------|------|
| Shard hours | 2 shards × 720 hours | 1,440 |
| Shard cost | 1,440 × $0.015/hour | $21.60 |
| PUT payload units | 52M records × 25KB units | 52M |
| PUT cost | 52M × $0.014/1M | $0.73 |
| Enhanced fan-out (3 consumers) | 3 × 720 × $0.015 | $32.40 |
| **Without enhanced fan-out** | | **$22.33** |
| **With enhanced fan-out** | | **$54.73** |

> Using standard consumers (polling) to reduce costs: **$36.00**

---

### 2. AWS Lambda (Consumers)

#### Consumer Functions

| Consumer | Invocations/Month | Duration | Memory | Cost |
|----------|-------------------|----------|--------|------|
| Dashboard Consumer | 1,500,000 | 200 ms | 512 MB | $6.25 |
| Geofence Consumer | 1,500,000 | 300 ms | 512 MB | $9.38 |
| Archive Consumer | 1,500,000 | 150 ms | 256 MB | $2.34 |
| GPS Producer | 2,160 | 500 ms | 256 MB | $0.01 |
| **Total** | | | | **$25.00** |

#### Batch Processing Benefits

- Kinesis batch size: 100 records
- Reduces Lambda invocations by 100x
- Cost without batching would be: $2,500/month

---

### 3. Amazon DynamoDB

#### Tables

| Table | Writes/Month | Reads/Month | Storage |
|-------|--------------|-------------|---------|
| TruckPositions | 52M | 10M | 2 GB |
| Geofences | 1,000 | 50M | 0.1 GB |
| Alerts | 15,000 | 30,000 | 0.5 GB |
| TruckStats | 3M | 5M | 1 GB |

#### Costs

| Item | Calculation | Cost |
|------|-------------|------|
| Write requests | 55M × $1.25/1M | $68.75 |
| Read requests | 65M × $0.25/1M | $16.25 |
| Storage | 3.6 GB × $0.25/GB | $0.90 |
| **With TTL (auto-delete old data)** | | **$30.00** |

> Using TTL to delete positions older than 24 hours reduces storage and write costs.

---

### 4. Amazon S3

#### Archive Storage

| Item | Calculation | Cost |
|------|-------------|------|
| Monthly data (Parquet) | 10 GB | |
| Storage (Standard) | 10 GB × $0.023/GB | $0.23 |
| Storage (IA, 30+ days) | 30 GB × $0.0125/GB | $0.38 |
| Storage (Glacier, 90+ days) | 60 GB × $0.004/GB | $0.24 |
| PUT requests | 50,000 × $0.005/1K | $0.25 |
| **Total** | | **$8.00** |

---

### 5. Amazon SNS

| Item | Calculation | Cost |
|------|-------------|------|
| Publish (alerts) | 15,000 × $0.50/1M | $0.01 |
| SMS notifications | 500 × $0.07/SMS | $35.00 |
| Email notifications | 15,000 × $0.00 | $0.00 |
| Lambda deliveries | 15,000 × $0.00 | $0.00 |
| **Without SMS** | | **$0.50** |
| **With SMS (500/month)** | | **$35.50** |

---

### 6. CloudWatch

| Item | Calculation | Cost |
|------|-------------|------|
| Logs ingestion | 15 GB × $0.50/GB | $7.50 |
| Logs storage | 15 GB × $0.03/GB | $0.45 |
| Custom metrics | 30 × $0.30 | $9.00 |
| Alarms | 15 × $0.10 | $1.50 |
| **Free tier offset** | | -$3.45 |
| **Total** | | **$15.00** |

---

## Cost Per Truck Analysis

### Monthly Cost Per Truck

| Fleet Size | Cost/Truck |
|------------|------------|
| 50 trucks | $2.80 |
| 100 trucks | $1.20 |
| 500 trucks | $0.50 |
| 1,000 trucks | $0.35 |

> Fixed costs (shards, CloudWatch) spread across fleet size.

---

## Cost Optimization Strategies

### 1. Kinesis Optimization

| Strategy | Savings | Notes |
|----------|---------|-------|
| Right-size shards | Variable | Monitor utilization |
| On-demand mode | Variable | For unpredictable traffic |
| Standard consumers | 60% | vs Enhanced fan-out |
| Longer batch intervals | 20-40% | Less frequent processing |

### 2. Lambda Optimization

| Strategy | Savings | Notes |
|----------|---------|-------|
| Increase batch size | 50%+ | Process more per invocation |
| Use Kinesis filtering | Variable | Process only relevant records |
| Graviton2 (ARM) | 20% | Lower compute cost |

### 3. DynamoDB Optimization

| Strategy | Savings | Notes |
|----------|---------|-------|
| TTL for positions | 70%+ | Delete old data automatically |
| DAX for geofence reads | 50% | Cache frequently accessed |
| Provisioned capacity | 40-60% | For predictable workloads |

### 4. Data Aggregation

| Strategy | Impact |
|----------|--------|
| Aggregate in Lambda | Store 1 record/minute instead of 12 |
| Pre-compute statistics | Reduce read operations |
| Compress S3 archives | 6x storage reduction |

---

## Scenario Comparisons

| Scenario | Fleet Size | Updates/Sec | Monthly Cost |
|----------|------------|-------------|--------------|
| **Small** | 25 trucks | 5/sec | $45-60 |
| **Medium** (Base) | 100 trucks | 20/sec | $100-140 |
| **Large** | 500 trucks | 100/sec | $400-550 |
| **Enterprise** | 2,000 trucks | 400/sec | $1,500-2,000 |

---

## Update Frequency Impact

| Frequency | Records/Month | Kinesis Cost | Lambda Cost | Total |
|-----------|---------------|--------------|-------------|-------|
| 1 second | 260M | $180 | $125 | $450 |
| 5 seconds | 52M | $36 | $25 | $120 |
| 15 seconds | 17M | $15 | $10 | $55 |
| 30 seconds | 9M | $10 | $6 | $40 |

> 5-second updates provide good balance of accuracy and cost.

---

## Annual Cost Projection

| Month | Fleet Size | Monthly Cost | Cumulative |
|-------|------------|--------------|------------|
| 1-3 | 100 | $120 | $360 |
| 4-6 | 150 | $160 | $840 |
| 7-9 | 200 | $200 | $1,440 |
| 10-12 | 250 | $240 | $2,160 |
| **Annual** | | | **$2,160** |

---

## Free Tier Coverage

| Service | Free Tier | Monthly Value |
|---------|-----------|---------------|
| Lambda | 1M requests, 400K GB-s | ~$8 |
| DynamoDB | 25 GB, 25 WCU/RCU | ~$15 |
| SNS | 1M publishes | ~$0.50 |
| CloudWatch | 10 metrics, 5 GB logs | ~$5 |
| S3 | 5 GB storage | ~$0.12 |
| **Total** | | **~$29/month** |

---

## Enterprise In-House Cost Comparison

Building and operating an equivalent real-time GPS tracking system in-house requires significant infrastructure, personnel, and ongoing operational costs.

### Infrastructure Costs (In-House)

| Component | Specification | Monthly Cost | Notes |
|-----------|---------------|--------------|-------|
| **Stream Processing Servers** | 4× servers (32 cores, 128GB RAM) | $2,400 | Apache Kafka cluster |
| **Application Servers** | 4× servers (16 cores, 64GB RAM) | $1,600 | Consumer applications |
| **Database Servers** | 2× servers (32 cores, 256GB RAM, NVMe) | $1,800 | Time-series database |
| **Storage Array** | 50TB SAN/NAS | $800 | Hot + warm storage |
| **Network Equipment** | Switches, routers, firewalls | $400 | 10Gbps backbone |
| **Load Balancers** | Hardware LB pair (HA) | $300 | F5/Citrix |
| **Backup Infrastructure** | Tape/disk backup system | $200 | DR capability |
| **Server Subtotal** | | **$7,500** | |

### Data Center / Facilities

| Item | Monthly Cost | Notes |
|------|--------------|-------|
| Colocation (10 racks) | $3,000 | Power, cooling, space |
| Power (20kW avg) | $2,400 | $0.12/kWh |
| Network bandwidth | $1,500 | 1Gbps dedicated |
| Physical security | $300 | 24/7 access |
| **Facilities Subtotal** | **$7,200** | |

### Software Licensing

| Software | Annual License | Monthly | Notes |
|----------|----------------|---------|-------|
| Apache Kafka (Confluent Enterprise) | $60,000 | $5,000 | Production support |
| TimescaleDB/InfluxDB Enterprise | $24,000 | $2,000 | Time-series DB |
| Redis Enterprise | $18,000 | $1,500 | Caching layer |
| Monitoring (Datadog/Splunk) | $24,000 | $2,000 | Full observability |
| Linux Enterprise (RHEL) | $12,000 | $1,000 | 10 servers |
| Backup software | $6,000 | $500 | Veeam/Commvault |
| **Software Subtotal** | | **$12,000** | |

### Personnel Costs

| Role | FTE | Annual Salary | Monthly (loaded) | Notes |
|------|-----|---------------|------------------|-------|
| DevOps/Platform Engineer | 1.0 | $140,000 | $14,583 | Kafka, infrastructure |
| Backend Developer | 1.5 | $130,000 | $20,313 | Stream processing |
| DBA | 0.5 | $120,000 | $6,250 | Time-series database |
| SRE/Operations | 0.5 | $130,000 | $6,771 | On-call, monitoring |
| Security Engineer | 0.25 | $150,000 | $3,906 | Security compliance |
| **Personnel Subtotal** | **3.75 FTE** | | **$51,823** | With 1.25x benefits multiplier |

### Total In-House Monthly Cost

| Category | Monthly Cost |
|----------|--------------|
| Infrastructure | $7,500 |
| Facilities | $7,200 |
| Software | $12,000 |
| Personnel | $51,823 |
| Contingency (10%) | $7,852 |
| **Total In-House** | **$86,375** |

### Cost Comparison Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│              AWS vs In-House Cost Comparison (100 trucks)               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  AWS Cloud          $120/month    ██░░░░░░░░░░░░░░░░░░░░░░░░░░  0.1%   │
│                                                                         │
│  In-House        $86,375/month    ████████████████████████████  100%   │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│  AWS Savings: $86,255/month (99.9%)                                     │
│  AWS Annual Savings: $1,035,060                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Scaling Comparison

| Fleet Size | AWS Monthly | In-House Monthly | AWS Advantage |
|------------|-------------|------------------|---------------|
| 25 trucks | $50 | $86,375 | 1,728x cheaper |
| 100 trucks | $120 | $86,375 | 720x cheaper |
| 500 trucks | $450 | $95,000 | 211x cheaper |
| 2,000 trucks | $1,800 | $120,000 | 67x cheaper |

> In-house costs don't scale linearly because infrastructure must be provisioned for peak capacity.

### Time-to-Market Comparison

| Phase | AWS | In-House |
|-------|-----|----------|
| Infrastructure setup | 1 day | 3-6 months |
| Development | 2-4 weeks | 4-8 months |
| Testing & QA | 1-2 weeks | 2-3 months |
| Production deployment | 1 day | 2-4 weeks |
| **Total** | **3-6 weeks** | **9-18 months** |

### Hidden In-House Costs Not Included

| Item | Impact |
|------|--------|
| Recruitment costs | $20,000-50,000 per hire |
| Training & certification | $5,000-15,000/year |
| Hardware refresh (3-year cycle) | 33% of hardware/year |
| Disaster recovery site | 50-100% of primary infrastructure |
| Compliance audits | $10,000-50,000/year |
| Insurance | Variable |
| Opportunity cost | Delayed time-to-market |

### Break-Even Analysis

At what scale does in-house become cost-competitive?

| Metric | Break-Even Point |
|--------|------------------|
| Fleet size | ~50,000+ trucks |
| Monthly data volume | 10+ TB processed |
| AWS monthly cost | ~$80,000+ |

> For most organizations, AWS remains significantly more cost-effective.

### When In-House Might Make Sense

1. **Extreme scale** - Processing billions of events/day
2. **Data sovereignty** - Strict regulatory requirements for on-premises data
3. **Existing infrastructure** - Sunk costs in data centers and staff
4. **Unique requirements** - Custom hardware or ultra-low latency needs

---

## Recommendations

1. **Use 5-second intervals** - Best balance of accuracy vs cost
2. **Enable Lambda batching** - Process 100 records per invocation
3. **Enable DynamoDB TTL** - Auto-delete positions after 24 hours
4. **Use S3 lifecycle policies** - Transition to Glacier after 90 days
5. **Monitor shard utilization** - Scale up/down based on traffic
6. **Consider Kinesis Data Firehose** - For direct S3 archival (simpler, may be cheaper)
