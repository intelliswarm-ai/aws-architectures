# AWS SMS - Multi-Engagement SMS Marketing Campaign

A customized text messaging service using Amazon Pinpoint for SMS marketing campaigns with real-time analytics via Amazon Kinesis Data Streams.

## Documentation

- [Business Logic Documentation](docs/BUSINESS_LOGIC.md) - Detailed business rules, data flows, and processing logic

## Use Case

A company is designing a customized text messaging service that targets its mobile app users. As part of its multi-engagement marketing campaign, the company needs to send a one-time confirmation message to all of its subscribers using Short Message Service (SMS). The system allows subscribers to reply to SMS messages.

**Key Requirements:**
- Customer responses must be kept for an entire year for analysis and targeted sale promotions
- SMS responses must be collected, processed, and analyzed in near-real-time
- Two-way SMS communication support

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│  ┌──────────────┐    ┌──────────────────────────────────────────────┐              │
│  │ Mobile App   │    │           Amazon Pinpoint                     │              │
│  │ Subscribers  │◀──▶│  - SMS Channel (Two-Way)                      │              │
│  │              │    │  - Journey (Multi-Engagement Campaign)        │              │
│  └──────────────┘    │  - Segments (Subscriber targeting)            │              │
│                      └───────────────────────┬──────────────────────┘              │
│                                              │                                      │
│                          Pinpoint Event Stream                                      │
│                                              │                                      │
│                                              ▼                                      │
│                      ┌──────────────────────────────────────────────┐              │
│                      │        Kinesis Data Stream                    │              │
│                      │  (sms-events-stream)                          │              │
│                      │  - 365 days retention                         │              │
│                      │  - Event collection & processing              │              │
│                      └───────────────────────┬──────────────────────┘              │
│                                              │                                      │
│           ┌──────────────────────────────────┼────────────────────────┐            │
│           │                                  │                        │            │
│           ▼                                  ▼                        ▼            │
│  ┌─────────────────┐            ┌─────────────────┐        ┌─────────────────┐    │
│  │ Real-Time       │            │ Response        │        │ Archive         │    │
│  │ Analytics       │            │ Processor       │        │ Processor       │    │
│  │ (Lambda)        │            │ (Lambda)        │        │ (Lambda)        │    │
│  └────────┬────────┘            └────────┬────────┘        └────────┬────────┘    │
│           │                              │                          │              │
│           ▼                              ▼                          ▼              │
│  ┌─────────────────┐            ┌─────────────────┐        ┌─────────────────┐    │
│  │ CloudWatch      │            │ DynamoDB        │        │ S3              │    │
│  │ (Metrics/Dash)  │            │ (Responses)     │        │ (365-day store) │    │
│  └─────────────────┘            └─────────────────┘        └─────────────────┘    │
│                                          │                          │              │
│                                          ▼                          ▼              │
│                                 ┌─────────────────┐        ┌─────────────────┐    │
│                                 │ SNS             │        │ Athena          │    │
│                                 │ (Notifications) │        │ (Analytics)     │    │
│                                 └─────────────────┘        └─────────────────┘    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Amazon Pinpoint SMS Channel
- **Two-Way SMS**: Enables subscribers to reply to messages
- **Dedicated Short Code/Long Code**: For sending and receiving SMS
- **SMS Sandbox**: Development and testing environment

### 2. Amazon Pinpoint Journey
- **Multi-Engagement Campaign**: Automated message sequences
- **Segment-Based Targeting**: Target specific subscriber groups
- **Journey Events**: Track message delivery, opens, and responses

### 3. Kinesis Data Stream (365-Day Retention)
- **Stream Name**: `sms-events-stream`
- **Retention Period**: 365 days (8760 hours)
- **Event Types**: SMS sent, delivered, failed, opted out, received (inbound)
- **Partition Key**: subscriber_id for ordered processing

### 4. Real-Time Analytics Consumer
- **Lambda Function**: Processes events for real-time dashboards
- **CloudWatch Metrics**: Delivery rates, response rates, opt-out rates
- **Use Case**: Marketing campaign performance monitoring

### 5. Response Processor
- **Lambda Function**: Processes inbound SMS responses
- **DynamoDB Table**: Stores responses with 1-year retention
- **SNS Topic**: Notifications for specific response patterns
- **Use Case**: Customer engagement tracking, targeted promotions

### 6. Archive Consumer
- **Lambda Function**: Archives all events for long-term analysis
- **S3 Bucket**: Stores data in Parquet format partitioned by date
- **Use Case**: Historical analytics, compliance, targeted promotions

## Technology Stack

- **Language**: Python 3.12
- **Infrastructure**: Terraform
- **AWS Services**:
  - Amazon Pinpoint (SMS Channel, Journeys)
  - Amazon Kinesis Data Streams
  - AWS Lambda
  - Amazon DynamoDB
  - Amazon S3
  - Amazon SNS
  - Amazon CloudWatch
  - AWS X-Ray

## Project Structure

```
aws-sms/
├── src/
│   ├── common/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration settings
│   │   ├── models.py           # Pydantic data models
│   │   ├── clients.py          # AWS client initialization
│   │   └── exceptions.py       # Custom exceptions
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── sms_event_processor.py   # Pinpoint event processor
│   │   ├── response_handler.py      # Inbound SMS response handler
│   │   ├── analytics_processor.py   # Real-time analytics
│   │   └── archive_consumer.py      # S3 archival processor
│   └── services/
│       ├── __init__.py
│       ├── pinpoint_service.py  # Pinpoint operations
│       ├── kinesis_service.py   # Kinesis operations
│       └── analytics_service.py # Analytics calculations
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars
│   └── modules/
│       ├── pinpoint/           # Pinpoint project, SMS, journey
│       ├── kinesis/            # Kinesis stream with 365-day retention
│       ├── lambda/             # Lambda functions
│       ├── dynamodb/           # Response storage
│       ├── s3/                 # Archive storage
│       ├── iam/                # IAM roles and policies
│       ├── sns/                # Notification topics
│       └── cloudwatch/         # Monitoring dashboards
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   ├── build.sh
│   ├── deploy.sh
│   └── test.sh
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Prerequisites

- Python 3.12+
- Terraform 1.5+
- AWS CLI configured with appropriate credentials
- SMS-enabled AWS account (request SMS sending quota if needed)

## Quick Start

### 1. Install Dependencies

```bash
cd aws-sms
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

### 3. Run Tests

```bash
./scripts/test.sh
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STREAM_NAME` | Kinesis stream name | `sms-events-stream` |
| `DYNAMODB_TABLE` | DynamoDB table for responses | `sms-responses` |
| `S3_BUCKET` | S3 bucket for archived data | `sms-archive-{account_id}` |
| `SNS_TOPIC_ARN` | SNS topic for notifications | - |
| `PINPOINT_APP_ID` | Pinpoint application ID | - |
| `LOG_LEVEL` | Logging level | `INFO` |

### Pinpoint SMS Configuration

**Two-Way SMS Setup:**
1. Request a dedicated long code or short code in AWS Pinpoint
2. Configure the SNS topic for incoming messages
3. Enable two-way SMS in the Pinpoint console

```json
{
  "two_way_channel_arn": "arn:aws:sns:region:account:sms-responses",
  "keyword_action": "AUTOMATIC_RESPONSE",
  "keywords": [
    {
      "keyword": "STOP",
      "action": "OPT_OUT"
    },
    {
      "keyword": "HELP",
      "action": "AUTOMATIC_RESPONSE",
      "response_text": "Reply STOP to unsubscribe. For help, visit our website."
    }
  ]
}
```

## Data Models

### SMS Event Record (from Pinpoint)

```json
{
  "event_type": "_SMS.SUCCESS",
  "event_timestamp": "2024-01-15T10:30:00.000Z",
  "arrival_timestamp": "2024-01-15T10:30:00.500Z",
  "application": {
    "app_id": "abc123",
    "sdk": {}
  },
  "client": {
    "client_id": "user-123"
  },
  "attributes": {
    "message_id": "msg-456",
    "destination_phone_number": "+1234567890",
    "record_status": "DELIVERED",
    "iso_country_code": "US",
    "message_type": "TRANSACTIONAL"
  },
  "metrics": {
    "price_in_millicents_usd": 645
  }
}
```

### Inbound SMS Response

```json
{
  "event_type": "_SMS.RECEIVED",
  "event_timestamp": "2024-01-15T10:35:00.000Z",
  "attributes": {
    "origination_number": "+1234567890",
    "destination_number": "+0987654321",
    "message_body": "YES",
    "keyword": "YES"
  }
}
```

### Response Analytics Record

```json
{
  "subscriber_id": "user-123",
  "phone_number": "+1234567890",
  "response_text": "YES",
  "response_timestamp": "2024-01-15T10:35:00Z",
  "campaign_id": "campaign-001",
  "journey_id": "journey-001",
  "sentiment": "positive",
  "ttl": 1736899200
}
```

## Kinesis 365-Day Retention Configuration

The Kinesis Data Stream is configured with 365-day retention (8760 hours) to meet the requirement of keeping customer responses for an entire year:

```hcl
resource "aws_kinesis_stream" "sms_events" {
  name             = "sms-events-stream"
  shard_count      = 2
  retention_period = 8760  # 365 days in hours

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}
```

**Cost Consideration**: Extended retention increases storage costs. For cost optimization, also archive to S3 using the archive consumer Lambda.

## Journey Configuration

### Multi-Engagement Campaign Example

```json
{
  "journey_name": "Welcome Series",
  "start_condition": {
    "segment_start_condition": {
      "segment_id": "new-subscribers"
    }
  },
  "activities": {
    "send_welcome": {
      "sms": {
        "message_config": {
          "message_type": "TRANSACTIONAL"
        },
        "template_name": "welcome-sms"
      },
      "next_activity": "wait_1_day"
    },
    "wait_1_day": {
      "wait": {
        "wait_time": {
          "wait_for": "1 day"
        }
      },
      "next_activity": "send_followup"
    },
    "send_followup": {
      "sms": {
        "message_config": {
          "message_type": "PROMOTIONAL"
        },
        "template_name": "followup-sms"
      }
    }
  }
}
```

## Monitoring

CloudWatch dashboards include:
- SMS delivery success rate
- SMS response rate
- Opt-out rate
- Kinesis stream throughput
- Lambda invocations and errors
- DynamoDB read/write capacity
- Cost per message

### Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `DeliverySuccessRate` | Percentage of delivered messages | < 95% |
| `ResponseRate` | Percentage of messages with responses | Monitoring only |
| `OptOutRate` | Percentage of opt-outs | > 5% |
| `KinesisIteratorAge` | Consumer lag in stream | > 60000 ms |

## Cost Optimization

- Use promotional message type when possible (lower cost)
- Set appropriate shard count based on actual throughput
- Use S3 Intelligent-Tiering for archived data
- Consider Kinesis Data Firehose for simplified archival
- Monitor and optimize Pinpoint spending

## Compliance

- **TCPA Compliance**: Ensure proper opt-in/opt-out handling
- **10DLC Registration**: Required for US A2P SMS
- **GDPR**: Data retention policies and right to erasure
- **Data Encryption**: All data encrypted at rest and in transit

## Multi-Cloud Deployment

### Service Mapping

| Component | AWS | Azure | GCP |
|-----------|-----|-------|-----|
| **SMS Service** | Pinpoint SMS | Azure Communication Services | Cloud Messaging (via Twilio) |
| **Stream Processing** | Kinesis Data Streams | Event Hubs | Pub/Sub |
| **Serverless Compute** | Lambda | Azure Functions | Cloud Functions |
| **NoSQL Database** | DynamoDB | Cosmos DB | Firestore |
| **Object Storage** | S3 | Blob Storage | Cloud Storage |
| **Messaging** | SNS | Service Bus | Pub/Sub |
| **Monitoring** | CloudWatch | Azure Monitor | Cloud Monitoring |

## License

This project is licensed under the MIT License.
