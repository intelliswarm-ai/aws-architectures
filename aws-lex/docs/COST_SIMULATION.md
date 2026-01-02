# AWS Lex Airline Chatbot - Cost Simulation

This document provides a detailed cost simulation for running the AWS Lex Airline Chatbot for one month. Costs are based on AWS pricing as of January 2025 for the **eu-central-2 (Zurich)** region.

## Table of Contents

1. [Scenario Overview](#scenario-overview)
2. [Cost Summary](#cost-summary)
3. [Detailed Cost Breakdown](#detailed-cost-breakdown)
4. [Cost Optimization Strategies](#cost-optimization-strategies)
5. [Scenario Comparisons](#scenario-comparisons)

---

## Scenario Overview

### Base Scenario: Medium Regional Airline

| Metric | Value |
|--------|-------|
| **Daily Conversations** | 500 |
| **Monthly Conversations** | 15,000 |
| **Avg Turns per Conversation** | 8 |
| **Monthly Requests (Text)** | 120,000 |
| **Voice Enabled** | No |
| **Bookings Created** | 2,000/month |
| **Check-Ins Processed** | 3,000/month |
| **Booking Modifications** | 500/month |

---

## Cost Summary

### Monthly Cost Estimate: Base Scenario

| Service | Monthly Cost (USD) | % of Total |
|---------|-------------------|------------|
| Amazon Lex V2 (Text) | $90.00 | 52.9% |
| AWS Lambda | $5.00 | 2.9% |
| Amazon DynamoDB | $25.00 | 14.7% |
| Amazon CloudWatch | $10.00 | 5.9% |
| API Gateway (Optional) | $15.00 | 8.8% |
| Other | $25.00 | 14.7% |
| **TOTAL** | **$170.00** | 100% |

```
┌────────────────────────────────────────────────────────────────┐
│                    Monthly Cost Distribution                    │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Lex V2           ██████████████████████████░░░░░░░░  52.9%    │
│  DynamoDB         ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░  14.7%    │
│  Other            ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░  14.7%    │
│  API Gateway      ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   8.8%    │
│  CloudWatch       ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   5.9%    │
│  Lambda           █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   2.9%    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Detailed Cost Breakdown

### 1. Amazon Lex V2

#### Text Requests

| Item | Calculation | Cost |
|------|-------------|------|
| Text requests | 120,000 × $0.00075 | $90.00 |
| **Free tier** | -10,000 requests (12 months) | -$7.50 |
| **Total (after free tier)** | | **$82.50** |

#### Speech Requests (If Enabled)

| Item | Calculation | Cost |
|------|-------------|------|
| Speech requests | 120,000 × $0.004 | $480.00 |
| Speech synthesis | 120,000 × $0.004 | $480.00 |
| **Total Speech** | | **$960.00** |

> Text-only mode is significantly cheaper than voice.

#### Lex Pricing Summary

| Request Type | Price per Request |
|--------------|-------------------|
| Text | $0.00075 |
| Speech (input) | $0.004 |
| Speech synthesis | $0.004 |
| Streaming speech | $0.0065 |

**Lex Monthly Total: $90.00**

---

### 2. AWS Lambda (Fulfillment)

#### Function Invocations

| Function | Invocations/Month | Duration | Memory | Cost |
|----------|-------------------|----------|--------|------|
| Lex Fulfillment | 120,000 | 500 ms | 256 MB | $2.50 |
| Dialog Code Hook | 60,000 | 200 ms | 256 MB | $0.50 |
| Validation Hook | 60,000 | 100 ms | 128 MB | $0.12 |
| **Total** | | | | **$5.00** |

#### Cost Calculation

| Item | Calculation | Cost |
|------|-------------|------|
| Requests | 240,000 × $0.20/1M | $0.05 |
| Compute GB-seconds | | |
| - Fulfillment | 120,000 × 0.5s × 0.25 GB | 15,000 GB-s |
| - Dialog Hook | 60,000 × 0.2s × 0.25 GB | 3,000 GB-s |
| - Validation | 60,000 × 0.1s × 0.125 GB | 750 GB-s |
| Total GB-seconds | 18,750 GB-s | |
| Cost | 18,750 × $0.0000166667 | $0.31 |
| **After Free Tier** | | **$5.00** |

---

### 3. Amazon DynamoDB

#### Tables

| Table | Writes/Month | Reads/Month | Storage |
|-------|--------------|-------------|---------|
| Flights | 1,000 | 100,000 | 0.5 GB |
| Bookings | 5,500 | 50,000 | 1 GB |
| CheckIns | 3,000 | 20,000 | 0.3 GB |

#### On-Demand Costs

| Item | Calculation | Cost |
|------|-------------|------|
| Write requests | 9,500 × $1.25/1M | $0.01 |
| Read requests | 170,000 × $0.25/1M | $0.04 |
| Storage | 1.8 GB × $0.25/GB | $0.45 |
| **Subtotal** | | **$0.50** |

#### Additional Features

| Feature | Cost |
|---------|------|
| Point-in-time recovery | $0.36 |
| On-demand backup | $0.18 |
| GSI (3 indices) | $5.00 |
| **Subtotal** | **$5.54** |

#### Provisioned Capacity (Alternative)

For predictable traffic, provisioned capacity may be cheaper:

| Item | WCU/RCU | Cost |
|------|---------|------|
| Write capacity | 5 WCU | $2.37 |
| Read capacity | 25 RCU | $2.97 |
| **Total** | | **$5.34** |

**DynamoDB Monthly Total: $25.00** (with buffer for spikes)

---

### 4. Amazon CloudWatch

| Item | Calculation | Cost |
|------|-------------|------|
| Log ingestion | 10 GB × $0.50/GB | $5.00 |
| Log storage | 10 GB × $0.03/GB | $0.30 |
| Custom metrics | 15 × $0.30 | $4.50 |
| Alarms | 5 × $0.10 | $0.50 |
| **Free tier offset** | | -$2.30 |
| **Total** | | **$10.00** |

---

### 5. API Gateway (Optional - for Web Integration)

| Item | Calculation | Cost |
|------|-------------|------|
| HTTP API requests | 500,000 × $1.00/1M | $0.50 |
| REST API requests | 100,000 × $3.50/1M | $0.35 |
| WebSocket connections | 50,000 × $0.25/1M | $0.01 |
| **Total** | | **$15.00** |

> API Gateway is optional if using direct Lex integration.

---

## Voice vs Text Cost Comparison

### Monthly Cost by Channel

| Channel | Requests | Unit Price | Monthly Cost |
|---------|----------|------------|--------------|
| **Text Only** | 120,000 | $0.00075 | $90 |
| **Voice Only** | 120,000 | $0.008 | $960 |
| **Mixed (70/30)** | 84K text + 36K voice | - | $351 |

### Channel Strategy

| Scenario | Recommendation | Monthly Cost |
|----------|----------------|--------------|
| Cost-optimized | Text-only (web/app) | $170 |
| Customer preference | Mixed channels | $400-500 |
| Premium experience | Full voice | $1,100+ |

---

## Intent-Based Cost Analysis

### Cost per Intent

| Intent | Avg Turns | Requests/Op | Ops/Month | Cost |
|--------|-----------|-------------|-----------|------|
| BookFlight | 10 | 10 | 2,000 | $15.00 |
| UpdateBooking | 6 | 6 | 500 | $2.25 |
| CheckIn | 5 | 5 | 3,000 | $11.25 |
| FallbackIntent | 3 | 3 | 5,000 | $11.25 |
| **Total** | | | | **$39.75** |

### Fallback Intent Optimization

High fallback rates increase costs without value:

| Fallback Rate | Extra Cost/Month | Action |
|---------------|------------------|--------|
| 5% | $4.50 | Acceptable |
| 15% | $13.50 | Review training |
| 30% | $27.00 | Urgent training needed |

---

## Conversation Analytics

### Success Rate Impact

| Completion Rate | Conversations | Requests | Cost |
|-----------------|---------------|----------|------|
| 95% (excellent) | 15,000 | 120,000 | $90 |
| 80% (good) | 15,000 | 142,500 | $107 |
| 60% (poor) | 15,000 | 190,000 | $143 |

> Poor NLU training increases costs due to longer conversations.

### Conversation Length Analysis

| Avg Turns | Requests/Month | Lex Cost | Impact |
|-----------|----------------|----------|--------|
| 5 turns | 75,000 | $56 | -38% |
| 8 turns (base) | 120,000 | $90 | baseline |
| 12 turns | 180,000 | $135 | +50% |

---

## Cost Optimization Strategies

### 1. Lex Optimization

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Text-only | 90% vs voice | Disable speech |
| Better NLU training | 20-40% | Reduce fallbacks |
| Slot confirmation | 10-20% | Fewer re-prompts |
| Intent chaining | 15-25% | Combine related intents |

### 2. Lambda Optimization

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Right-size memory | 20-30% | 256 MB is often sufficient |
| Reduce duration | 15-25% | Optimize code |
| SnapStart | 30% cold start | For Java |
| ARM64 | 20% | Graviton2 |

### 3. DynamoDB Optimization

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Provisioned capacity | 30-50% | For predictable load |
| Reserved capacity | Up to 77% | 1-3 year commitment |
| TTL cleanup | Variable | Auto-delete old bookings |
| Sparse indices | Variable | Index only needed attributes |

### 4. Architecture Optimization

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Lex response cards | Fewer turns | Guide user choices |
| Quick replies | Fewer turns | Reduce typing errors |
| Context carryover | 20-30% | Maintain session state |

---

## Scenario Comparisons

| Scenario | Daily Conversations | Voice | Monthly Cost |
|----------|---------------------|-------|--------------|
| **Startup** | 100 | No | $45-60 |
| **Regional** (Base) | 500 | No | $150-200 |
| **National** | 2,000 | Mixed | $600-800 |
| **Enterprise** | 10,000 | Yes | $3,500-5,000 |

---

## Multi-Language Support

### Additional Language Costs

| Language | NLU Quality | Extra Training |
|----------|-------------|----------------|
| English (US/UK) | Excellent | None |
| Spanish | Excellent | None |
| French | Good | Minimal |
| German | Good | Minimal |
| Other | Variable | May need custom |

### Multi-Language Architecture

| Approach | Cost Impact | Notes |
|----------|-------------|-------|
| Single bot, multiple locales | +0% | Built-in Lex feature |
| Separate bots per language | +50-100% | More maintenance |
| Translation layer | +20-30% | Add Translate API |

---

## Annual Cost Projection

### With Growth

| Quarter | Daily Conversations | Monthly Cost | Quarterly |
|---------|---------------------|--------------|-----------|
| Q1 | 500 | $170 | $510 |
| Q2 | 750 | $230 | $690 |
| Q3 | 1,000 | $300 | $900 |
| Q4 | 1,500 | $420 | $1,260 |
| **Annual** | | | **$3,360** |

### With Voice Addition (Q3)

| Quarter | Channel | Monthly Cost | Quarterly |
|---------|---------|--------------|-----------|
| Q1-Q2 | Text | $200 | $1,200 |
| Q3-Q4 | Mixed (50/50) | $550 | $3,300 |
| **Annual** | | | **$4,500** |

---

## Free Tier Coverage

| Service | Free Tier | Monthly Value |
|---------|-----------|---------------|
| Lex V2 | 10,000 text, 5,000 speech (12 mo) | ~$10 |
| Lambda | 1M requests, 400K GB-s | ~$8 |
| DynamoDB | 25 GB, 25 WCU/RCU | ~$15 |
| CloudWatch | 10 metrics, 5 GB logs | ~$5 |
| **Total** | | **~$38/month** |

---

## ROI Analysis

### Chatbot vs Human Agent

| Metric | Human Agent | Lex Chatbot |
|--------|-------------|-------------|
| Cost per conversation | $5-15 | $0.01 |
| Availability | 8-16 hours | 24/7 |
| Languages | 1-2 | Many |
| Scalability | Linear cost | Near-zero marginal |
| Response time | 2-5 minutes | Instant |

### Monthly Savings Calculation

| Conversations | Human Cost | Chatbot Cost | Savings |
|---------------|------------|--------------|---------|
| 5,000 | $25,000-75,000 | $60 | 99%+ |
| 15,000 | $75,000-225,000 | $170 | 99%+ |
| 50,000 | $250,000-750,000 | $500 | 99%+ |

### Break-Even Analysis

| Investment | Human FTE Equivalent | Payback |
|------------|---------------------|---------|
| $10,000 (development) | 0.5 FTE | 1-2 months |
| $170/month (operation) | 0.01 FTE | Immediate |

---

## Compliance Considerations

### PCI-DSS (Payment Data)

| Requirement | Implementation | Cost Impact |
|-------------|----------------|-------------|
| Slot obfuscation | Built-in | $0 |
| Conversation logs | Encrypted | +$5/month |
| Audit trail | CloudTrail | +$2/month |

### GDPR

| Requirement | Implementation | Cost Impact |
|-------------|----------------|-------------|
| Data deletion | DynamoDB TTL | $0 |
| Consent tracking | Custom slot | +$0 |
| Right to export | Lambda function | +$1/month |

---

## Recommendations

1. **Start with text-only** - Voice adds 10x cost
2. **Invest in NLU training** - Reduce fallback rate to <10%
3. **Use response cards** - Reduce conversation turns
4. **Monitor conversation metrics** - Track success rate and turns
5. **Consider multi-language early** - Lex handles it natively
6. **Use session attributes** - Reduce re-prompting
7. **Implement context carryover** - Smoother conversations

