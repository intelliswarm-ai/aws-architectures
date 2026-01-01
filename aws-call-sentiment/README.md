# AWS Call Sentiment Analysis Platform

A serverless solution for analyzing customer service call transcripts using Amazon Comprehend for sentiment analysis, with results indexed to Amazon OpenSearch for visualization and insights.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         CALL SENTIMENT ANALYSIS PLATFORM                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────────┐    │
│   │   S3 Bucket  │────▶│   Lambda     │────▶│      Amazon Comprehend           │    │
│   │ (Transcripts)│     │  (Trigger)   │     │   (Sentiment Analysis Job)       │    │
│   └──────────────┘     └──────────────┘     └──────────────────────────────────┘    │
│         │                                              │                            │
│         │                                              ▼                            │
│         │              ┌──────────────┐     ┌──────────────────────────────────┐    │
│         │              │   Lambda     │◀────│      S3 Bucket                   │    │
│         │              │  (Indexer)   │     │   (Comprehend Output)            │    │
│         │              └──────────────┘     └──────────────────────────────────┘    │
│         │                    │                                                      │
│         │                    ▼                                                      │
│         │              ┌──────────────────────────────────────────┐                 │
│         │              │         Amazon OpenSearch                │                 │
│         │              │    ┌────────────────────────────────┐    │                 │
│         │              │    │  call-sentiment-* indices      │    │                 │
│         │              │    │  - transcripts                 │    │                 │
│         │              │    │  - sentiments                  │    │                 │
│         │              │    │  - aggregations                │    │                 │
│         │              │    └────────────────────────────────┘    │                 │
│         │              │    ┌────────────────────────────────┐    │                 │
│         │              │    │  OpenSearch Dashboards         │    │                 │
│         │              │    │  - Sentiment trends            │    │                 │
│         │              │    │  - Agent performance           │    │                 │
│         │              │    │  - Call analytics              │    │                 │
│         │              │    └────────────────────────────────┘    │                 │
│         │              └──────────────────────────────────────────┘                 │
│         │                                                                           │
│   ┌─────┴──────────────────────────────────────────────────────────────────────┐    │
│   │                          API Gateway (REST)                                │    │
│   │   POST /analyze    - Start sentiment analysis                              │    │
│   │   GET  /calls      - Query analyzed calls                                  │    │
│   │   GET  /stats      - Get aggregated statistics                             │    │
│   │   GET  /agents     - Get agent performance metrics                         │    │
│   └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Automatic Transcript Processing**: S3 event triggers Lambda when new transcripts arrive
- **Batch Sentiment Analysis**: Amazon Comprehend batch jobs for efficient processing
- **Real-time Analysis**: On-demand sentiment analysis via REST API
- **OpenSearch Integration**: Full-text search and analytics on call data
- **Interactive Dashboards**: Pre-built OpenSearch dashboards for visualization
- **Entity Extraction**: Identify key phrases, entities, and topics from calls
- **Multi-language Support**: Detect and analyze calls in multiple languages

## Use Case

A company analyzing customer service calls to:
- Identify customer satisfaction trends
- Monitor agent performance
- Detect escalation patterns
- Extract common issues and topics
- Generate actionable insights for training

## Project Structure

```
aws-call-sentiment/
├── README.md
├── pyproject.toml
├── src/
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── transcript_processor.py    # S3 trigger handler
│   │   ├── comprehend_handler.py      # Start Comprehend jobs
│   │   ├── result_indexer.py          # Index results to OpenSearch
│   │   ├── api_handler.py             # REST API endpoints
│   │   └── job_status_handler.py      # Check job status
│   ├── services/
│   │   ├── __init__.py
│   │   ├── comprehend_service.py      # Comprehend API wrapper
│   │   ├── opensearch_service.py      # OpenSearch operations
│   │   ├── transcript_service.py      # Transcript parsing
│   │   └── analytics_service.py       # Analytics aggregations
│   └── common/
│       ├── __init__.py
│       ├── models.py                  # Pydantic data models
│       ├── config.py                  # Configuration settings
│       └── exceptions.py              # Custom exceptions
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
│       ├── s3/                        # Transcript & output buckets
│       ├── comprehend/                # Comprehend IAM & config
│       ├── opensearch/                # OpenSearch domain
│       ├── lambda/                    # Lambda functions
│       ├── api_gateway/               # REST API
│       ├── iam/                       # IAM roles & policies
│       ├── cloudwatch/                # Monitoring & alarms
│       └── eventbridge/               # Event rules
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   ├── build.sh
│   ├── deploy.sh
│   ├── test.sh
│   └── destroy.sh
└── docs/
    └── BUSINESS_LOGIC.md
```

## Transcript Format

Expected JSON format for call transcripts:

```json
{
  "callId": "call-12345",
  "timestamp": "2024-01-15T10:30:00Z",
  "duration": 325,
  "agentId": "agent-001",
  "agentName": "John Smith",
  "customerId": "cust-67890",
  "customerPhone": "+1234567890",
  "queueName": "support",
  "language": "en",
  "segments": [
    {
      "speaker": "AGENT",
      "startTime": 0.0,
      "endTime": 5.2,
      "text": "Thank you for calling support, how may I help you today?"
    },
    {
      "speaker": "CUSTOMER",
      "startTime": 5.5,
      "endTime": 15.3,
      "text": "I've been having issues with my account for the past week and no one has been able to help me."
    }
  ],
  "metadata": {
    "source": "connect",
    "recordingUrl": "s3://recordings/call-12345.wav"
  }
}
```

## Prerequisites

- Python 3.12+
- AWS CLI configured
- Terraform 1.5+
- pip or uv for package management

## Quick Start

### 1. Deploy Infrastructure

```bash
cd aws-call-sentiment

# Initialize and deploy
./scripts/build.sh
./scripts/deploy.sh -e dev
```

### 2. Upload Transcripts

```bash
# Upload a transcript file
aws s3 cp sample-transcript.json s3://call-sentiment-dev-transcripts/input/

# Upload multiple files
aws s3 sync ./transcripts/ s3://call-sentiment-dev-transcripts/input/
```

### 3. Access OpenSearch Dashboards

After deployment, access the OpenSearch Dashboards URL from Terraform outputs:

```bash
terraform output opensearch_dashboard_url
```

### 4. Query via API

```bash
# Get call statistics
curl -X GET https://{api-gateway-url}/stats

# Search calls by sentiment
curl -X GET "https://{api-gateway-url}/calls?sentiment=NEGATIVE&limit=10"

# Get agent performance
curl -X GET "https://{api-gateway-url}/agents/agent-001/metrics"
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| TRANSCRIPTS_BUCKET | S3 bucket for input transcripts | - |
| OUTPUT_BUCKET | S3 bucket for Comprehend output | - |
| OPENSEARCH_ENDPOINT | OpenSearch domain endpoint | - |
| COMPREHEND_ROLE_ARN | IAM role for Comprehend jobs | - |
| LOG_LEVEL | Logging level | INFO |

### Terraform Variables

```hcl
# terraform.tfvars
environment           = "dev"
aws_region            = "eu-central-2"
opensearch_instance   = "t3.small.search"
opensearch_node_count = 2
retention_days        = 90
```

## OpenSearch Index Mappings

### call-transcripts index

```json
{
  "mappings": {
    "properties": {
      "callId": { "type": "keyword" },
      "timestamp": { "type": "date" },
      "agentId": { "type": "keyword" },
      "customerId": { "type": "keyword" },
      "duration": { "type": "integer" },
      "fullText": { "type": "text", "analyzer": "standard" },
      "sentiment": { "type": "keyword" },
      "sentimentScore": {
        "properties": {
          "positive": { "type": "float" },
          "negative": { "type": "float" },
          "neutral": { "type": "float" },
          "mixed": { "type": "float" }
        }
      },
      "entities": {
        "type": "nested",
        "properties": {
          "text": { "type": "text" },
          "type": { "type": "keyword" },
          "score": { "type": "float" }
        }
      },
      "keyPhrases": { "type": "text" },
      "language": { "type": "keyword" }
    }
  }
}
```

## Dashboard Visualizations

The pre-configured OpenSearch dashboards include:

1. **Sentiment Overview**
   - Sentiment distribution (pie chart)
   - Sentiment trend over time (line chart)
   - Average sentiment scores

2. **Agent Performance**
   - Calls per agent (bar chart)
   - Average sentiment by agent
   - Negative call percentage by agent

3. **Call Analytics**
   - Call volume over time
   - Average call duration
   - Peak hours heatmap

4. **Entity Analysis**
   - Top mentioned entities
   - Common key phrases (word cloud)
   - Topic clustering

## Cost Considerations

| Service | Pricing |
|---------|---------|
| Amazon Comprehend | $0.0001/unit (sentiment), $0.0001/unit (entities) |
| Amazon OpenSearch | ~$0.036/hour (t3.small.search) |
| Lambda | $0.20/1M requests |
| S3 | $0.023/GB/month |
| API Gateway | $3.50/1M requests |

**Tip**: Use Comprehend batch jobs for cost efficiency when processing multiple transcripts.

## Security

- OpenSearch deployed in VPC with fine-grained access control
- Lambda functions in private subnets
- IAM roles with least-privilege policies
- S3 bucket encryption (SSE-S3)
- API Gateway with API key authentication

## Monitoring

CloudWatch dashboards provide:
- Lambda invocation metrics
- Comprehend job success/failure rates
- OpenSearch cluster health
- API Gateway latency and errors
- S3 storage metrics

## License

This project is for educational and demonstration purposes.
