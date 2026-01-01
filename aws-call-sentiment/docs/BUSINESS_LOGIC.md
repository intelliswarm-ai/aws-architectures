# Business Logic Documentation - AWS Call Sentiment Analysis

## Overview

The AWS Call Sentiment Analysis platform processes customer service call transcripts to extract sentiment, entities, and key insights using Amazon Comprehend, with results indexed to Amazon OpenSearch for visualization and analytics.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       CALL SENTIMENT ANALYSIS PLATFORM                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                        DATA INGESTION LAYER                              │   │
│  │                                                                          │   │
│  │   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐     │   │
│  │   │  S3 Bucket   │────────▶│   Lambda     │────────▶│  Comprehend  │     │   │
│  │   │ (Transcripts)│  Event  │ (Processor)  │  API    │  (Analysis)  │     │   │
│  │   │  input/      │         │              │         │              │     │   │
│  │   └──────────────┘         └──────────────┘         └──────────────┘     │   │
│  │                                                            │             │   │
│  └────────────────────────────────────────────────────────────┼─────────────┘   │
│                                                               │                 │
│  ┌────────────────────────────────────────────────────────────┼─────────────┐   │
│  │                        STORAGE & INDEXING                  ▼             │   │
│  │                                                                          │   │
│  │   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐     │   │
│  │   │  S3 Bucket   │         │   Lambda     │────────▶│  OpenSearch  │     │   │
│  │   │  (Output)    │────────▶│  (Indexer)   │         │   Domain     │     │   │
│  │   │              │  Event  │              │         │              │     │   │
│  │   └──────────────┘         └──────────────┘         └──────────────┘     │   │
│  │                                                            │             │   │
│  └────────────────────────────────────────────────────────────┼─────────────┘   │
│                                                               │                 │
│  ┌────────────────────────────────────────────────────────────┼─────────────┐   │
│  │                        API & VISUALIZATION                 ▼             │   │
│  │                                                                          │   │
│  │   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐     │   │
│  │   │ API Gateway  │────────▶│   Lambda     │────────▶│  OpenSearch  │     │   │
│  │   │  (REST)      │         │  (API)       │  Query  │  Dashboards  │     │   │
│  │   │              │         │              │         │              │     │   │
│  │   └──────────────┘         └──────────────┘         └──────────────┘     │   │
│  │                                                                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Core Data Flows

### 1. Real-Time Transcript Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  REAL-TIME PROCESSING FLOW                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Transcript Upload (S3 input/)                                 │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ S3 Event Notification                                   │   │
│   │   • Triggered on ObjectCreated                          │   │
│   │   • Filter: input/*.json                                │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Lambda: Transcript Processor                            │   │
│   │                                                         │   │
│   │   1. Parse S3 event (bucket, key)                       │   │
│   │   2. Download and parse JSON transcript                 │   │
│   │   3. Validate transcript structure                      │   │
│   │   4. Extract full text from segments                    │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Amazon Comprehend Analysis                              │   │
│   │                                                         │   │
│   │   Language Detection:                                   │   │
│   │     detect_dominant_language(full_text)                 │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Sentiment Analysis (3 calls):                         │   │
│   │     • Overall: detect_sentiment(full_text)              │   │
│   │     • Customer: detect_sentiment(customer_segments)     │   │
│   │     • Agent: detect_sentiment(agent_segments)           │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Entity Extraction:                                    │   │
│   │     detect_entities(full_text)                          │   │
│   │     → PERSON, ORGANIZATION, LOCATION, DATE, etc.        │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Key Phrase Extraction:                                │   │
│   │     detect_key_phrases(full_text)                       │   │
│   │     → Top 20 phrases by confidence                      │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Create CallAnalysis Object                              │   │
│   │   • call_id, timestamp, duration                        │   │
│   │   • agent_id, customer_id                               │   │
│   │   • overall_sentiment + score                           │   │
│   │   • customer_sentiment, agent_sentiment                 │   │
│   │   • entities[], key_phrases[]                           │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Index to OpenSearch                                     │   │
│   │   • Index: call-sentiment-transcripts                   │   │
│   │   • Document ID: call_id                                │   │
│   │   • Full-text search on fullText, keyPhrases            │   │
│   │   • Aggregations on sentiment, agentId, timestamp       │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   Return processing result                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Batch Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     BATCH PROCESSING FLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   EventBridge Schedule (Daily 2AM UTC)                          │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Lambda: Comprehend Handler                              │   │
│   │                                                         │   │
│   │   1. List transcripts in input/batch/ prefix            │   │
│   │   2. Parse each transcript JSON                         │   │
│   │   3. Extract full text                                  │   │
│   │   4. Format for Comprehend (one doc per line)           │   │
│   │   5. Upload to S3 output bucket                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Start Comprehend Batch Job                              │   │
│   │                                                         │   │
│   │   start_sentiment_detection_job():                      │   │
│   │     • InputDataConfig: s3://output/batch-xxx/input.txt  │   │
│   │     • OutputDataConfig: s3://output/batch-xxx/output/   │   │
│   │     • DataAccessRoleArn: comprehend-role                │   │
│   │     • LanguageCode: en                                  │   │
│   │                                                         │   │
│   │   Returns: job_id, status                               │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Job Processing (Async)                                  │   │
│   │                                                         │   │
│   │   Status progression:                                   │   │
│   │     SUBMITTED → IN_PROGRESS → COMPLETED                 │   │
│   │                             → FAILED                    │   │
│   │                                                         │   │
│   │   On completion: Results written to S3 output path      │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ S3 Event → Lambda: Result Indexer                       │   │
│   │                                                         │   │
│   │   1. Download result files (tar.gz or JSON)             │   │
│   │   2. Parse Comprehend output (one result per line)      │   │
│   │   3. Map results to original transcripts                │   │
│   │   4. Index to OpenSearch                                │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. API Query Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                       API QUERY FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Client Request                                                │
│     GET /calls?sentiment=NEGATIVE&agent_id=agent-001            │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ API Gateway                                             │   │
│   │   • API Key validation                                  │   │
│   │   • Rate limiting (50 req/sec, 10K/day)                 │   │
│   │   • Route to Lambda                                     │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Lambda: API Handler                                     │   │
│   │                                                         │   │
│   │   Parse query parameters:                               │   │
│   │     • sentiment (filter)                                │   │
│   │     • agent_id (filter)                                 │   │
│   │     • customer_id (filter)                              │   │
│   │     • date_from, date_to (range)                        │   │
│   │     • q (full-text search)                              │   │
│   │     • page, page_size (pagination)                      │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ OpenSearch Query                                        │   │
│   │                                                         │   │
│   │   {                                                     │   │
│   │     "query": {                                          │   │
│   │       "bool": {                                         │   │
│   │         "filter": [                                     │   │
│   │           {"term": {"sentiment": "NEGATIVE"}},          │   │
│   │           {"term": {"agentId": "agent-001"}}            │   │
│   │         ]                                               │   │
│   │       }                                                 │   │
│   │     },                                                  │   │
│   │     "sort": [{"timestamp": "desc"}],                    │   │
│   │     "from": 0, "size": 20                               │   │
│   │   }                                                     │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   Return JSON response                                          │
│     {                                                           │
│       "total": 150,                                             │
│       "page": 1,                                                │
│       "calls": [...]                                            │
│     }                                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Models

### Call Transcript (Input)

| Field | Type | Description |
|-------|------|-------------|
| callId | String | Unique call identifier |
| timestamp | DateTime | Call start time |
| duration | Integer | Duration in seconds |
| agentId | String | Agent identifier |
| agentName | String | Agent display name |
| customerId | String | Customer identifier |
| customerPhone | String | Customer phone number |
| queueName | String | Call queue/department |
| language | String | Language code (default: en) |
| segments | Array | List of transcript segments |
| metadata | Object | Additional metadata |

### Transcript Segment

| Field | Type | Description |
|-------|------|-------------|
| speaker | Enum | AGENT, CUSTOMER, UNKNOWN |
| startTime | Float | Segment start time (seconds) |
| endTime | Float | Segment end time (seconds) |
| text | String | Spoken text |

### Call Analysis (Output)

| Field | Type | Description |
|-------|------|-------------|
| callId | String | Reference to original call |
| transcript | CallTranscript | Full transcript data |
| overall_sentiment | SentimentResult | Full call sentiment |
| customer_sentiment | SentimentResult | Customer-only sentiment |
| agent_sentiment | SentimentResult | Agent-only sentiment |
| entities | Array[EntityResult] | Extracted entities |
| key_phrases | Array[KeyPhraseResult] | Key phrases |
| analyzed_at | DateTime | Analysis timestamp |

### Sentiment Result

| Field | Type | Description |
|-------|------|-------------|
| sentiment | Enum | POSITIVE, NEGATIVE, NEUTRAL, MIXED |
| score.positive | Float | Confidence (0-1) |
| score.negative | Float | Confidence (0-1) |
| score.neutral | Float | Confidence (0-1) |
| score.mixed | Float | Confidence (0-1) |

## Sentiment Analysis Logic

### Classification Rules

```
┌─────────────────────────────────────────────────────────────────┐
│                   SENTIMENT CLASSIFICATION                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Amazon Comprehend Returns:                                    │
│                                                                 │
│   {                                                             │
│     "Sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL" | "MIXED", │
│     "SentimentScore": {                                         │
│       "Positive": 0.85,                                         │
│       "Negative": 0.05,                                         │
│       "Neutral": 0.08,                                          │
│       "Mixed": 0.02                                             │
│     }                                                           │
│   }                                                             │
│                                                                 │
│   Dominant Sentiment = max(Positive, Negative, Neutral, Mixed)  │
│                                                                 │
│   Business Interpretation:                                      │
│                                                                 │
│   POSITIVE (score > 0.6):                                       │
│     • Customer satisfied with resolution                        │
│     • Pleasant interaction                                      │
│     • Successful service delivery                               │
│                                                                 │
│   NEGATIVE (score > 0.6):                                       │
│     • Customer frustrated or angry                              │
│     • Unresolved issue                                          │
│     • Poor service experience                                   │
│     → Triggers review/escalation workflow                       │
│                                                                 │
│   NEUTRAL (score > 0.5):                                        │
│     • Factual, informational exchange                           │
│     • No strong emotion detected                                │
│     • Standard service interaction                              │
│                                                                 │
│   MIXED:                                                        │
│     • Both positive and negative sentiment                      │
│     • Complex interaction                                       │
│     • May require manual review                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Customer vs Agent Sentiment

```
┌───────────────────────────────────────────────────────────────────┐
│                  SPEAKER-SPECIFIC ANALYSIS                        │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│   Customer Sentiment (Primary KPI):                               │
│     • Extract all CUSTOMER speaker segments                       │
│     • Concatenate text                                            │
│     • Analyze separately                                          │
│     → Measures customer satisfaction                              │
│                                                                   │
│   Agent Sentiment (Quality Metric):                               │
│     • Extract all AGENT speaker segments                          │
│     • Analyze separately                                          │
│     → Measures agent professionalism                              │
│                                                                   │
│   Business Rules:                                                 │
│                                                                   │
│   IF customer_sentiment = NEGATIVE AND agent_sentiment =POSITIVE: │
│     → Agent handled difficult customer well                       │
│     → Positive agent review                                       │
│                                                                   │
│   IF customer_sentiment = NEGATIVE AND agent_sentiment = NEGATIVE:│ 
│     → Both parties frustrated                                     │
│     → Review call for training opportunity                        │
│                                                                   │
│   IF customer_sentiment = POSITIVE AND agent_sentiment = POSITIVE:│
│     → Successful interaction                                      │
│     → Model call for training                                     │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Entity Extraction

### Supported Entity Types

| Type | Examples | Business Use |
|------|----------|--------------|
| PERSON | "John Smith" | Customer/contact identification |
| ORGANIZATION | "Acme Corp" | Company mentions |
| LOCATION | "New York" | Geographic tracking |
| DATE | "next Monday" | Scheduling, deadlines |
| QUANTITY | "three items" | Order details |
| COMMERCIAL_ITEM | "iPhone 15" | Product mentions |
| EVENT | "annual review" | Event tracking |

### Entity Processing

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTITY EXTRACTION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Input: "I've been waiting since Monday for my iPhone delivery"│
│                                                                 │
│   Output:                                                       │
│   [                                                             │
│     {                                                           │
│       "text": "Monday",                                         │
│       "type": "DATE",                                           │
│       "score": 0.95                                             │
│     },                                                          │
│     {                                                           │
│       "text": "iPhone",                                         │
│       "type": "COMMERCIAL_ITEM",                                │
│       "score": 0.89                                             │
│     }                                                           │
│   ]                                                             │
│                                                                 │
│   Business Application:                                         │
│     • Track product mentions in negative calls                  │
│     • Identify trending issues by entity                        │
│     • Route calls based on product/service mentioned            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Analytics & Aggregations

### Dashboard Metrics

```
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYTICS METRICS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Overall Metrics (Configurable Period):                        │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ total_calls:       1,234                                │   │
│   │ positive_calls:    456 (37.0%)                          │   │
│   │ negative_calls:    123 (10.0%)                          │   │
│   │ neutral_calls:     589 (47.7%)                          │   │
│   │ mixed_calls:       66 (5.3%)                            │   │
│   │ avg_duration:      287 seconds                          │   │
│   │ avg_positive_score: 0.42                                │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   Trend Analysis:                                               │
│     • Sentiment over time (daily/weekly/monthly)                │
│     • Comparison with previous period                           │
│     • Percentage change indicators                              │
│                                                                 │
│   Agent Performance:                                            │
│     • Calls per agent                                           │
│     • Satisfaction rate by agent                                │
│     • Average call duration by agent                            │
│     • Top entities mentioned per agent                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Quality Score Calculation

```
┌─────────────────────────────────────────────────────────────────┐
│                   QUALITY SCORE ALGORITHM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Base Score: 50 points                                         │
│                                                                 │
│   Sentiment Component (±30 points):                             │
│     POSITIVE: +30                                               │
│     NEUTRAL:  +15                                               │
│     MIXED:    +5                                                │
│     NEGATIVE: -10                                               │
│                                                                 │
│   Customer Sentiment Component (±20 points):                    │
│     POSITIVE: +20                                               │
│     NEUTRAL:  +10                                               │
│     MIXED:    0                                                 │
│     NEGATIVE: -15                                               │
│                                                                 │
│   Duration Penalty:                                             │
│     < 60 seconds:  -5 (too short, likely unresolved)            │
│     > 600 seconds: -10 (too long, inefficient)                  │
│                                                                 │
│   Final Score = clamp(0, 100, calculated_score)                 │
│                                                                 │
│   Score Interpretation:                                         │
│     80-100: Excellent interaction                               │
│     60-79:  Good interaction                                    │
│     40-59:  Average, room for improvement                       │
│     20-39:  Below average, review needed                        │
│     0-19:   Poor, immediate attention required                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## OpenSearch Index Design

### Index Mapping

```json
{
  "mappings": {
    "properties": {
      "callId": { "type": "keyword" },
      "timestamp": { "type": "date" },
      "duration": { "type": "integer" },
      "agentId": { "type": "keyword" },
      "customerId": { "type": "keyword" },
      "queueName": { "type": "keyword" },
      "language": { "type": "keyword" },
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
      "keyPhrases": { "type": "text" }
    }
  }
}
```

### Common Queries

| Query Type | OpenSearch DSL |
|------------|----------------|
| Filter by sentiment | `{"term": {"sentiment": "NEGATIVE"}}` |
| Filter by agent | `{"term": {"agentId": "agent-001"}}` |
| Date range | `{"range": {"timestamp": {"gte": "2024-01-01"}}}` |
| Full-text search | `{"multi_match": {"query": "refund", "fields": ["fullText", "keyPhrases"]}}` |
| Aggregation | `{"aggs": {"by_sentiment": {"terms": {"field": "sentiment"}}}}` |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/calls` | GET | List/search calls with filters |
| `/calls/{call_id}` | GET | Get specific call analysis |
| `/stats` | GET | Dashboard summary metrics |
| `/stats/trend` | GET | Sentiment trend over time |
| `/agents` | GET | List top agents by performance |
| `/agents/{agent_id}/metrics` | GET | Agent-specific metrics |
| `/insights` | GET | Call insights and recommendations |

## Error Handling

### Comprehend API Limits

| Limit | Value | Handling |
|-------|-------|----------|
| Text size | 5,000 bytes | Truncate with warning |
| Batch size | 25 documents | Split into batches |
| Requests/sec | 20 | Exponential backoff |
| Concurrent jobs | 10 | Queue excess jobs |

### Exception Hierarchy

```
CallSentimentError (base)
├── TranscriptParseError
│   └── Invalid JSON, missing fields
├── ComprehendError
│   └── API failures, throttling
├── OpenSearchError
│   └── Index, query failures
└── ValidationError
    └── Invalid input data
```

## Cost Optimization

### Comprehend Pricing Strategy

| Approach | Cost | Use Case |
|----------|------|----------|
| Real-time API | $0.0001/unit | Low volume, immediate results |
| Batch jobs | $0.00005/unit | High volume, delayed results |
| Async jobs | $0.00005/unit | Large documents |

### Optimization Strategies

1. **Batch Processing**: Use batch jobs for non-urgent analysis
2. **Text Truncation**: Limit to 5,000 bytes per call
3. **Selective Analysis**: Skip entity/key phrase for simple sentiment
4. **Caching**: Cache frequent OpenSearch queries
5. **Data Lifecycle**: Archive old data to S3 Glacier

## Monitoring & Alerting

### Key Metrics

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Lambda errors | > 5 in 5 min | SNS notification |
| OpenSearch cluster red | Any | Immediate alert |
| Comprehend job failures | > 3 consecutive | Review required |
| API latency p99 | > 5 seconds | Performance review |

### Dashboard Widgets

- Lambda invocations/errors by function
- OpenSearch cluster health (green/yellow/red)
- Sentiment distribution over time
- API Gateway request/error rates
