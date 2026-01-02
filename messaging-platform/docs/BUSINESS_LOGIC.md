# SMS Marketing System - Business Logic Documentation

This document describes the business logic, data flows, and processing rules for the SMS Marketing System built on Amazon Pinpoint and Kinesis.

## Table of Contents

1. [System Overview](#system-overview)
2. [Data Flow Architecture](#data-flow-architecture)
3. [SMS Campaign Management](#sms-campaign-management)
4. [Event Processing Pipeline](#event-processing-pipeline)
5. [Response Handling Logic](#response-handling-logic)
6. [Subscriber Lifecycle Management](#subscriber-lifecycle-management)
7. [Analytics and Metrics](#analytics-and-metrics)
8. [Data Retention and Archival](#data-retention-and-archival)
9. [Compliance and Regulatory](#compliance-and-regulatory)

---

## System Overview

### Purpose

The SMS Marketing System enables businesses to:
- Send targeted SMS campaigns to mobile app subscribers
- Collect and process subscriber responses in near-real-time
- Maintain response data for 365 days for analysis and targeted promotions
- Handle opt-in/opt-out requests automatically
- Generate real-time analytics on campaign performance

### Core Business Requirements

| Requirement | Implementation |
|-------------|----------------|
| Send confirmation SMS to subscribers | Amazon Pinpoint Journeys with SMS templates |
| Allow subscribers to reply | Two-way SMS via Pinpoint SMS Channel |
| Store responses for 1 year | Kinesis (365-day retention) + DynamoDB (TTL) + S3 Archive |
| Near-real-time processing | Lambda consumers with Kinesis triggers |
| Targeted sale promotions | Response analytics and sentiment tracking |

---

## Data Flow Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            OUTBOUND FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Marketing Team          Pinpoint Journey           Subscriber              │
│  ┌──────────┐           ┌──────────────┐          ┌──────────┐              │
│  │ Create   │──────────▶│ Execute      │─────────▶│ Receive  │              │
│  │ Campaign │           │ Multi-step   │          │ SMS      │              │
│  └──────────┘           │ Journey      │          └──────────┘              │
│                         └──────┬───────┘                                    │
│                                │                                            │
│                                ▼                                            │
│                         ┌──────────────┐                                    │
│                         │ Event Stream │                                    │
│                         │ to Kinesis   │                                    │
│                         └──────────────┘                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            INBOUND FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Subscriber              Pinpoint SMS              Processing               │
│  ┌──────────┐           ┌──────────────┐          ┌──────────────┐          │
│  │ Reply    │──────────▶│ Receive      │─────────▶│ Kinesis      │          │
│  │ to SMS   │           │ Inbound SMS  │          │ Stream       │          │
│  └──────────┘           └──────────────┘          └──────┬───────┘          │
│                                                          │                  │
│                    ┌─────────────────────────────────────┼──────────┐       │
│                    │                    │                │          │       │
│                    ▼                    ▼                ▼          ▼       │
│              ┌──────────┐        ┌──────────┐    ┌──────────┐ ┌──────────┐  │
│              │ Response │        │ Analytics│    │ Archive  │ │ Event    │  │
│              │ Handler  │        │ Processor│    │ Consumer │ │ Processor│  │
│              └──────────┘        └──────────┘    └──────────┘ └──────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Event Types

| Event Type | Source | Description |
|------------|--------|-------------|
| `_SMS.SUCCESS` | Pinpoint | SMS successfully delivered to carrier |
| `_SMS.FAILURE` | Pinpoint | SMS delivery failed |
| `_SMS.BUFFERED` | Pinpoint | SMS queued for delivery |
| `_SMS.OPTOUT` | Pinpoint | Subscriber opted out via carrier |
| `_SMS.RECEIVED` | Pinpoint | Inbound SMS received from subscriber |

---

## SMS Campaign Management

### Journey Types

#### 1. Welcome Series Journey
```
Trigger: New subscriber added to segment
    │
    ▼
┌─────────────────────────────────────┐
│ Step 1: Send Welcome SMS            │
│ Template: "Welcome! Reply YES to    │
│ confirm or STOP to unsubscribe."    │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ Step 2: Wait 24 hours               │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ Step 3: Check if confirmed          │
│ ┌─────────────┬─────────────┐       │
│ │ YES         │ NO          │       │
│ └──────┬──────┴──────┬──────┘       │
│        │             │              │
│        ▼             ▼              │
│   Send Promo    Send Reminder       │
│   SMS           SMS                 │
└─────────────────────────────────────┘
```

#### 2. Promotional Campaign Journey
```
Trigger: Scheduled or segment-based
    │
    ▼
┌─────────────────────────────────────┐
│ Filter: subscription_status=ACTIVE  │
│         opt_in_timestamp EXISTS     │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ Send Promotional SMS                │
│ Template with personalization:      │
│ "Hi {{name}}, use code {{promo}}    │
│ for {{discount}}% off!"             │
└─────────────────────────────────────┘
```

### Message Types

| Type | Use Case | Cost | Regulations |
|------|----------|------|-------------|
| TRANSACTIONAL | Confirmations, OTPs, alerts | Higher priority | Less restricted |
| PROMOTIONAL | Marketing, offers, newsletters | Lower cost | More restricted, quiet hours apply |

---

## Event Processing Pipeline

### Lambda Consumer Architecture

Each Lambda consumer processes events from the same Kinesis stream but with different responsibilities:

```
                    Kinesis Data Stream
                    (365-day retention)
                           │
           ┌───────────────┼───────────────┬───────────────┐
           │               │               │               │
           ▼               ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ Event       │ │ Response    │ │ Analytics   │ │ Archive     │
    │ Processor   │ │ Handler     │ │ Processor   │ │ Consumer    │
    ├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────┤
    │ All SMS     │ │ _SMS.       │ │ All SMS     │ │ All SMS     │
    │ events      │ │ RECEIVED    │ │ events      │ │ events      │
    │             │ │ only        │ │             │ │             │
    ├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────┤
    │ Logging &   │ │ Store       │ │ Calculate   │ │ Archive to  │
    │ Monitoring  │ │ responses   │ │ metrics     │ │ S3          │
    │             │ │ Handle      │ │ Publish to  │ │             │
    │             │ │ opt-in/out  │ │ CloudWatch  │ │             │
    └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### Processing Flow per Consumer

#### Event Processor (`sms_event_processor.py`)
```python
for record in kinesis_batch:
    event = parse_sms_event(record)

    # Log for monitoring
    log_event(event)

    # Track delivery metrics
    if event.type == SUCCESS:
        increment_metric("DeliverySuccess")
    elif event.type == FAILURE:
        increment_metric("DeliveryFailed")
    elif event.type == OPTOUT:
        increment_metric("OptOut")
    elif event.type == RECEIVED:
        increment_metric("ResponseReceived")
```

#### Response Handler (`response_handler.py`)
```python
for record in kinesis_batch:
    if record.event_type != "_SMS.RECEIVED":
        continue

    inbound = parse_inbound_sms(record)

    # Store response for 365 days
    store_response_in_dynamodb(inbound, ttl=365_days)

    # Handle special keywords
    if is_opt_out(inbound.message):      # STOP, UNSUBSCRIBE, CANCEL
        process_opt_out(inbound)
    elif is_confirmation(inbound.message): # YES, Y, CONFIRM, OK
        process_confirmation(inbound)
    else:
        # Regular response - analyze for promotions
        analyze_for_targeting(inbound)
```

---

## Response Handling Logic

### Keyword Recognition

The system recognizes standard SMS keywords and processes them automatically:

#### Opt-Out Keywords
| Keyword | Action | Response Sent |
|---------|--------|---------------|
| STOP | Unsubscribe | "You have been unsubscribed. Reply START to subscribe again." |
| UNSUBSCRIBE | Unsubscribe | Same as STOP |
| CANCEL | Unsubscribe | Same as STOP |
| END | Unsubscribe | Same as STOP |
| QUIT | Unsubscribe | Same as STOP |

#### Opt-In / Confirmation Keywords
| Keyword | Action | Response Sent |
|---------|--------|---------------|
| YES | Confirm subscription | "Thank you for confirming! You're now subscribed to our updates." |
| Y | Confirm subscription | Same as YES |
| CONFIRM | Confirm subscription | Same as YES |
| OK | Confirm subscription | Same as YES |
| 1 | Confirm subscription | Same as YES |
| START | Re-subscribe | "Welcome back! You're now subscribed." |

### Response Processing Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│                    INBOUND SMS RECEIVED                         │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Normalize Response                                      │
│ - Trim whitespace                                               │
│ - Convert to uppercase                                          │
│ - Extract first word if multiple                                │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Generate Subscriber ID                                  │
│ - Hash phone number: SHA256(phone)[:16]                         │
│ - Ensures consistent ID across interactions                     │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Store Response in DynamoDB                              │
│ - subscriber_id (PK)                                            │
│ - response_timestamp (SK)                                       │
│ - response_text, normalized_response                            │
│ - sentiment (positive/negative/neutral)                         │
│ - TTL = current_time + 365 days                                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Check for Special Keywords                              │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
            ┌───────────┐ ┌───────────┐ ┌───────────┐
            │ OPT-OUT   │ │ OPT-IN    │ │ REGULAR   │
            │ Keyword   │ │ Keyword   │ │ Response  │
            └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
                  │             │             │
                  ▼             ▼             ▼
            ┌───────────┐ ┌───────────┐ ┌───────────┐
            │ Update    │ │ Update    │ │ Analyze   │
            │ Pinpoint  │ │ Pinpoint  │ │ Sentiment │
            │ OptOut=ALL│ │ OptOut=   │ │ for       │
            │           │ │ NONE      │ │ Targeting │
            └─────┬─────┘ └─────┬─────┘ └───────────┘
                  │             │
                  ▼             ▼
            ┌───────────┐ ┌───────────┐
            │ Update    │ │ Update    │
            │ Subscriber│ │ Subscriber│
            │ status=   │ │ status=   │
            │ opted_out │ │ active    │
            └─────┬─────┘ └─────┬─────┘
                  │             │
                  ▼             ▼
            ┌───────────┐ ┌───────────┐
            │ Send      │ │ Send      │
            │ OptOut    │ │ Confirm   │
            │ Confirm   │ │ Message   │
            └───────────┘ └───────────┘
```

### Sentiment Analysis

Simple keyword-based sentiment analysis for response categorization:

```python
POSITIVE_INDICATORS = {
    "yes", "y", "ok", "great", "thanks", "thank", "love", "awesome",
    "confirm", "interested", "buy", "want", "order", "1"
}

NEGATIVE_INDICATORS = {
    "no", "n", "stop", "cancel", "unsubscribe", "hate", "spam",
    "never", "remove", "delete", "quit", "end", "0"
}

def analyze_sentiment(response_text):
    words = set(response_text.lower().split())

    if words & POSITIVE_INDICATORS:
        return "positive"
    elif words & NEGATIVE_INDICATORS:
        return "negative"
    else:
        return "neutral"
```

---

## Subscriber Lifecycle Management

### Subscriber States

```
                    ┌──────────────────────────────────┐
                    │                                  │
                    ▼                                  │
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ NEW     │───▶│ PENDING │───▶│ ACTIVE  │───▶│ OPTED   │
│         │    │         │    │         │    │ OUT     │
└─────────┘    └─────────┘    └─────────┘    └────┬────┘
                    │                              │
                    │         ┌────────────────────┘
                    │         │ (Reply START)
                    │         ▼
                    │    ┌─────────┐
                    └───▶│ BOUNCED │
                         └─────────┘
```

### State Transitions

| From State | To State | Trigger | Action |
|------------|----------|---------|--------|
| NEW | PENDING | Added to segment | Send welcome SMS |
| PENDING | ACTIVE | Reply YES/CONFIRM | Update Pinpoint, send confirmation |
| PENDING | OPTED_OUT | Reply STOP | Update Pinpoint OptOut=ALL |
| ACTIVE | OPTED_OUT | Reply STOP | Update Pinpoint OptOut=ALL |
| OPTED_OUT | ACTIVE | Reply START | Update Pinpoint OptOut=NONE |
| ANY | BOUNCED | Carrier rejection | Mark as undeliverable |

### Subscriber Record Structure

```json
{
  "subscriber_id": "a1b2c3d4e5f67890",
  "phone_number": "+1234567890",
  "subscription_status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "opt_in_timestamp": "2024-01-02T14:22:00Z",
  "opt_out_timestamp": null,
  "total_messages_sent": 15,
  "total_responses": 3,
  "last_response_at": "2024-01-15T10:30:00Z",
  "attributes": {
    "segment": "high_value",
    "preferred_time": "morning",
    "language": "en"
  }
}
```

---

## Analytics and Metrics

### Real-Time Metrics (CloudWatch)

| Metric | Namespace | Unit | Description |
|--------|-----------|------|-------------|
| MessagesDelivered | SMS/Marketing | Count | Successfully delivered SMS |
| MessagesFailed | SMS/Marketing | Count | Failed SMS deliveries |
| ResponsesReceived | SMS/Marketing | Count | Inbound SMS received |
| OptOuts | SMS/Marketing | Count | Opt-out requests processed |
| DeliveryRate | SMS/Marketing | Percent | Delivered / Sent * 100 |
| ResponseRate | SMS/Marketing | Percent | Responses / Delivered * 100 |
| TotalCostUSD | SMS/Marketing | None | Cumulative SMS cost |

### Campaign-Specific Metrics

| Metric | Dimensions | Description |
|--------|------------|-------------|
| CampaignMessagesDelivered | CampaignId | Deliveries per campaign |
| CampaignDeliveryRate | CampaignId | Success rate per campaign |
| CampaignResponseRate | CampaignId | Response rate per campaign |

### Country-Specific Metrics

| Metric | Dimensions | Description |
|--------|------------|-------------|
| MessagesDeliveredByCountry | Country | Deliveries per country |
| MessagesFailedByCountry | Country | Failures per country |
| CostByCountry | Country | Cost per country |

### Analytics Calculations

```python
# Delivery Rate
delivery_rate = messages_delivered / messages_sent

# Response Rate
response_rate = responses_received / messages_delivered

# Opt-Out Rate
opt_out_rate = opt_outs / messages_delivered

# Cost per Message
cost_per_message = total_cost_usd / messages_sent

# Cost per Response
cost_per_response = total_cost_usd / responses_received
```

---

## Data Retention and Archival

### Retention Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA RETENTION TIMELINE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Day 0          Day 30         Day 90         Day 365        Day 365+       │
│    │              │              │               │              │           │
│    ▼              ▼              ▼               ▼              ▼           │
│ ┌───────┐      ┌──────┐      ┌──────┐       ┌──────┐       ┌──────┐         │
│ │Kinesis│      │ S3   │      │ S3   │       │ S3   │       │Delete│         │
│ │Stream │      │Stand-│      │Glacer│       │Deep  │       │ or   │         │
│ │       │      │ard   │      │IR    │       │Archve│       │Archve│         │
│ └───────┘      └──────┘      └──────┘       └──────┘       └──────┘         │
│    │              │              │               │              │           │
│    │              │              │               │              │           │
│ ┌──────┐      ┌──────┐      ┌──────┐       ┌──────┐       ┌──────┐          │
│ │Dynamo│      │Dynamo│      │Dynamo│       │Dynamo│       │ TTL  │          │
│ │  DB  │      │  DB  │      │  DB  │       │  DB  │       │Expire│          │
│ │Active│      │Active│      │Active│       │Active│       │      │          │
│ └──────┘      └──────┘      └──────┘       └──────┘       └──────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Storage Tiers

| Storage | Retention | Access Pattern | Cost |
|---------|-----------|----------------|------|
| Kinesis Stream | 365 days | Real-time replay | $$$ |
| DynamoDB | 365 days (TTL) | Query by subscriber/campaign | $$ |
| S3 Standard | 0-30 days | Frequent analytics | $$ |
| S3 Intelligent-Tiering | 30-90 days | Auto-optimized | $ |
| S3 Glacier IR | 90-365 days | Occasional access | ¢ |
| S3 Deep Archive | 365+ days | Compliance/audit | ¢¢ |

### Archive Record Format

Events are archived in JSONL (newline-delimited JSON) format, gzipped:

```
s3://bucket/events/year=2024/month=01/day=15/events_103045123456.jsonl.gz
```

Each line contains:
```json
{
  "event_type": "_SMS.SUCCESS",
  "event_timestamp": "2024-01-15T10:30:45.123Z",
  "subscriber_id": "a1b2c3d4e5f67890",
  "phone_number": "+1234567890",
  "message_id": "msg-abc123",
  "campaign_id": "camp-001",
  "journey_id": "journey-001",
  "record_status": "DELIVERED",
  "message_type": "PROMOTIONAL",
  "country_code": "US",
  "price_millicents": 645,
  "response_text": null,
  "archived_at": "2024-01-15T10:31:00.000Z"
}
```

---

## Compliance and Regulatory

### TCPA Compliance (US)

| Requirement | Implementation |
|-------------|----------------|
| Prior express consent | Opt-in confirmation flow |
| Honor opt-out requests | Automatic STOP processing |
| Identify sender | Sender ID in messages |
| Time restrictions | Journey scheduling (no nights/weekends for promo) |

### GDPR Compliance (EU)

| Requirement | Implementation |
|-------------|----------------|
| Right to access | DynamoDB query by subscriber_id |
| Right to erasure | Manual deletion endpoint + TTL |
| Data portability | S3 archive export |
| Consent tracking | opt_in_timestamp stored |

### 10DLC Registration (US A2P)

For Application-to-Person messaging in the US:
1. Register brand with The Campaign Registry (TCR)
2. Register campaign use case
3. Obtain approved 10-digit long code
4. Configure in Pinpoint SMS channel

### Data Encryption

| Data State | Encryption Method |
|------------|-------------------|
| Kinesis at rest | AWS KMS (aws/kinesis) |
| DynamoDB at rest | AWS managed encryption |
| S3 at rest | AWS KMS with bucket key |
| In transit | TLS 1.2+ |

---

## Appendix: Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STREAM_NAME` | Kinesis stream name | `sms-events-stream` |
| `RESPONSES_TABLE` | DynamoDB responses table | `sms-responses` |
| `SUBSCRIBERS_TABLE` | DynamoDB subscribers table | `subscribers` |
| `ARCHIVE_BUCKET` | S3 archive bucket | `sms-archive-{account}` |
| `NOTIFICATIONS_TOPIC` | SNS topic for alerts | - |
| `PINPOINT_APP_ID` | Pinpoint application ID | - |
| `TTL_DAYS` | Response retention days | `365` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Kinesis Consumer Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Batch Size | 100 | Balance throughput vs latency |
| Parallelization | 2 | Process multiple batches per shard |
| Max Batching Window | 5 seconds | Near-real-time with batching efficiency |
| Starting Position | LATEST | Process new events only |
| Retry Attempts | 3 | Handle transient failures |
