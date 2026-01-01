# Business Logic Documentation - AWS ML Platform

## Overview

The AWS ML Platform is an intelligent document processing system that demonstrates comprehensive AWS Machine Learning capabilities. It provides an end-to-end pipeline for ingesting, extracting, analyzing, and generating insights from documents using multiple AWS AI/ML services.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           INTELLIGENT DOCUMENT PROCESSING                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐    │
│  │  Upload  │───▶│  Ingestion  │───▶│  Extraction  │───▶│     Analysis     │    │
│  │  (S3)    │    │  (Lambda)   │    │  (Textract/  │    │  (Comprehend/    │    │
│  └──────────┘    └─────────────┘    │  Transcribe) │    │   Rekognition)   │    │
│                                     └──────────────┘    └──────────────────┘    │
│                                                                  │              │
│                                                                  ▼              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────┐       │
│  │   Notification   │◀───│   Finalization   │◀───│   Classification     │       │
│  │     (SNS)        │    │    (Lambda)      │    │    (SageMaker)       │       │
│  └──────────────────┘    └──────────────────┘    └──────────────────────┘       │
│                                                           │                     │
│                                                           ▼                     │
│                                               ┌──────────────────────┐          │
│                                               │     Generation       │          │
│                                               │     (Bedrock)        │          │
│                                               └──────────────────────┘          │
│                                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐     │
│  │                    AWS Step Functions Orchestration                    │     │
│  │                                                                        │     │
│  │   ValidateDocument ──▶ RouteByType ──▶ Extract/Transcribe/Image        │     │
│  │          │                                       │                     │     │
│  │          ▼                                       ▼                     │     │
│  │   AnalyzeContent ──▶ ClassifyDocument ──▶ GenerateInsights             │     │
│  │          │                                       │                     │     │
│  │          ▼                                       ▼                     │     │
│  │   FinalizeProcessing ──────────────────▶ NotifySuccess                 │     │
│  └────────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Document Processing States

```
PENDING ──▶ INGESTED ──▶ EXTRACTING ──▶ EXTRACTED
                                            │
                                            ▼
               COMPLETED ◀── GENERATING ◀── CLASSIFYING ◀── ANALYZING ◀── ANALYZED
                   │
                   ▼
              [SUCCESS]

[At any point] ──▶ FAILED (with error_message)
```

## Core Data Flows

### 1. Document Ingestion Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      DOCUMENT INGESTION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   S3 Upload Event                                               │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Parse S3 Event Metadata                                 │   │
│   │   • Extract bucket name                                 │   │
│   │   • Extract object key                                  │   │
│   │   • Get file size and content type                      │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Validate Document                                       │   │
│   │   • Check file is in input/ folder                      │   │
│   │   • Verify file size limits                             │   │
│   │   • Validate file type                                  │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Detect Document Type                                    │   │
│   │   • PDF: application/pdf, .pdf                          │   │
│   │   • IMAGE: image/*, .jpg, .png, .gif                    │   │
│   │   • AUDIO: audio/*, .mp3, .wav, .m4a                    │   │
│   │   • TEXT: text/*, .txt, .csv                            │   │
│   │   • UNKNOWN: other types                                │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Create Document Record                                  │   │
│   │   • Generate UUID document_id                           │   │
│   │   • Store in DynamoDB with status: INGESTED             │   │
│   │   • Set created_at timestamp                            │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   Start Step Functions Execution                                │
│        │                                                        │
│        ▼                                                        │
│   Return document_id & workflow ARN                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Text Extraction Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      TEXT EXTRACTION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Receive Document Context                                      │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Check File Size                                         │   │
│   │   • < 5MB: Use synchronous API                          │   │
│   │   • >= 5MB: Use asynchronous API                        │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ├──────────────────────┬──────────────────────────────   │
│        ▼                      ▼                                 │
│   ┌──────────────┐    ┌──────────────────────────────────┐      │
│   │ Sync Textract│    │ Async Textract                   │      │
│   │ detect_doc.. │    │   • start_document_text_detection│      │
│   │              │    │   • Poll for completion          │      │
│   │              │    │   • get_document_text_detection  │      │
│   └──────────────┘    └──────────────────────────────────┘      │
│        │                      │                                 │
│        └──────────────────────┴──────────────────────────────   │
│                      │                                          │
│                      ▼                                          │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Parse Textract Response                                 │   │
│   │   • Extract LINE blocks → full text                     │   │
│   │   • Count WORD blocks                                   │   │
│   │   • Calculate average confidence                        │   │
│   │   • Extract tables (if TABLES feature)                  │   │
│   │   • Extract forms (if FORMS feature)                    │   │
│   │   • Get page count from metadata                        │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   Return ExtractionResult                                       │
│     • extracted_text                                            │
│     • confidence                                                │
│     • pages, words                                              │
│     • tables, forms                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Audio Transcription Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     AUDIO TRANSCRIPTION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Receive Audio Document                                        │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Start Transcription Job                                 │   │
│   │   • Generate unique job name                            │   │
│   │   • Set media URI (S3 location)                         │   │
│   │   • Configure language (optional auto-detect)           │   │
│   │   • Set output location                                 │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Poll for Completion                                     │   │
│   │   • Check status every 10 seconds                       │   │
│   │   • Maximum wait: 600 seconds                           │   │
│   │   • Handle IN_PROGRESS, COMPLETED, FAILED               │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Extract Transcript                                      │   │
│   │   • Retrieve transcript from result URL                 │   │
│   │   • Parse JSON for text content                         │   │
│   │   • Count words                                         │   │
│   │   • Delete transcription job (cleanup)                  │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   Return ExtractionResult with transcript                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Content Analysis Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      CONTENT ANALYSIS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Amazon Comprehend (for text content)                    │   │
│   │                                                         │   │
│   │   detect_dominant_language()                            │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   detect_entities()                                     │   │
│   │     • PERSON, LOCATION, ORGANIZATION                    │   │
│   │     • DATE, QUANTITY, EVENT                             │   │
│   │     • Returns: text, type, score, offsets               │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   detect_sentiment()                                    │   │
│   │     • POSITIVE, NEGATIVE, NEUTRAL, MIXED                │   │
│   │     • Confidence scores for each                        │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   detect_key_phrases()                                  │   │
│   │     • Top 20 phrases by confidence score                │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   detect_pii_entities() [if enabled]                    │   │
│   │     • SSN, PHONE, EMAIL, ADDRESS, etc.                  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Amazon Rekognition (for image content)                  │   │
│   │                                                         │   │
│   │   detect_labels()                                       │   │
│   │     • Top 50 labels with >70% confidence                │   │
│   │     • Objects, scenes, concepts                         │   │
│   │     • Categories and hierarchies                        │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   detect_text()                                         │   │
│   │     • OCR for text in images                            │   │
│   │     • Lines with >70% confidence                        │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   detect_moderation_labels() [if enabled]               │   │
│   │     • Inappropriate content detection                   │   │
│   │     • Violence, adult content, etc.                     │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   Return AnalysisResult                                         │
│     • entities, key_phrases, sentiment                          │
│     • language, pii_entities                                    │
│     • image_labels, detected_text, moderation_labels            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5. Document Classification Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCUMENT CLASSIFICATION                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Build Feature Vector                                          │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Feature Engineering                                     │   │
│   │                                                         │   │
│   │   Text Statistics:                                      │   │
│   │     • word_count (from extraction)                      │   │
│   │     • page_count                                        │   │
│   │     • extraction_confidence                             │   │
│   │     • has_tables (boolean)                              │   │
│   │     • has_forms (boolean)                               │   │
│   │                                                         │   │
│   │   NLP Features:                                         │   │
│   │     • entity_count                                      │   │
│   │     • key_phrase_count                                  │   │
│   │     • has_pii (boolean)                                 │   │
│   │     • sentiment (categorical)                           │   │
│   │     • language (code)                                   │   │
│   │                                                         │   │
│   │   Image Features:                                       │   │
│   │     • image_label_count                                 │   │
│   │     • is_moderation_flagged                             │   │
│   │     • top 5 key phrases                                 │   │
│   │     • top 5 image labels                                │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ├──────────────────────┬──────────────────────────────   │
│        ▼                      ▼                                 │
│   ┌──────────────────┐  ┌────────────────────────────────────┐  │
│   │ SageMaker        │  │ Rule-Based Fallback                │  │
│   │ Endpoint         │  │                                    │  │
│   │                  │  │ IF keywords match:                 │  │
│   │ invoke_endpoint  │  │   "invoice/payment" → INVOICE      │  │
│   │ with features    │  │   "contract/terms" → CONTRACT      │  │
│   │                  │  │   "report/findings" → REPORT       │  │
│   │                  │  │   "resume/skills" → RESUME         │  │
│   │                  │  │   otherwise → OTHER                │  │
│   └──────────────────┘  └────────────────────────────────────┘  │
│        │                      │                                 │
│        └──────────────────────┴──────────────────────────────   │
│                      │                                          │
│                      ▼                                          │
│   Return InferenceResult                                        │
│     • predicted_class                                           │
│     • confidence                                                │
│     • probabilities (all classes)                               │
│     • model_version                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6. Insight Generation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     INSIGHT GENERATION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Prepare Document Context                                      │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Amazon Bedrock (Claude 3 Sonnet)                        │   │
│   │                                                         │   │
│   │   Comprehensive Prompt:                                 │   │
│   │   ┌───────────────────────────────────────────────────┐ │   │
│   │   │ Analyze this document and provide:                │ │   │
│   │   │                                                   │ │   │
│   │   │ 1. SUMMARY (2-3 paragraphs, max 500 words)        │ │   │
│   │   │    - Main themes and key points                   │ │   │
│   │   │    - Important findings or conclusions            │ │   │
│   │   │                                                   │ │   │
│   │   │ 2. Q&A PAIRS (5 question-answer pairs)            │ │   │
│   │   │    - Questions a reader might ask                 │ │   │
│   │   │    - Concise, accurate answers                    │ │   │
│   │   │                                                   │ │   │
│   │   │ 3. TOPICS (up to 10 topics)                       │ │   │
│   │   │    - Main subjects covered                        │ │   │
│   │   │    - Key themes and categories                    │ │   │
│   │   │                                                   │ │   │
│   │   │ 4. ACTION ITEMS                                   │ │   │
│   │   │    - Tasks or follow-ups mentioned                │ │   │
│   │   │    - Recommendations for action                   │ │   │
│   │   └───────────────────────────────────────────────────┘ │   │
│   │                                                         │   │
│   │   Response: JSON format                                 │   │
│   │   Token tracking: input_tokens, output_tokens           │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Parse Response                                          │   │
│   │   • Extract JSON from model response                    │   │
│   │   • Fallback parsing for malformed JSON                 │   │
│   │   • Validate structure                                  │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   Return GenerativeResult                                       │
│     • summary                                                   │
│     • questions [{question, answer}, ...]                       │
│     • topics [topic1, topic2, ...]                              │
│     • action_items [item1, item2, ...]                          │
│     • model_id, input_tokens, output_tokens                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Models

### Document Model

| Field | Type | Description |
|-------|------|-------------|
| document_id | UUID | Unique identifier |
| bucket | String | S3 bucket name |
| key | String | S3 object key |
| document_type | Enum | PDF, IMAGE, AUDIO, TEXT, UNKNOWN |
| status | Enum | Processing state |
| file_size | Integer | File size in bytes |
| content_type | String | MIME type |
| created_at | DateTime | Creation timestamp (UTC) |
| updated_at | DateTime | Last update timestamp (UTC) |
| metadata | Dict | Nested processing results |
| error_message | String | Error details if FAILED |
| retry_count | Integer | Number of retry attempts |

### ExtractionResult Model

| Field | Type | Description |
|-------|------|-------------|
| document_id | String | Reference to document |
| extracted_text | String | Full extracted text |
| confidence | Float | Average confidence (0.0-1.0) |
| language | String | Detected language code |
| pages | Integer | Page count |
| words | Integer | Word count |
| tables | List[Dict] | Extracted table data |
| forms | List[Dict] | Extracted form key-value pairs |

### AnalysisResult Model

| Field | Type | Description |
|-------|------|-------------|
| document_id | String | Reference to document |
| entities | List[EntityResult] | Named entities with type and score |
| key_phrases | List[String] | Top 20 key phrases |
| sentiment | SentimentResult | Sentiment with confidence scores |
| language | String | Language code |
| pii_entities | List[EntityResult] | PII detected |
| image_labels | List[ImageLabel] | Image labels with confidence |
| detected_text | List[String] | Text detected in images |
| moderation_labels | List[Dict] | Content moderation flags |

### InferenceResult Model

| Field | Type | Description |
|-------|------|-------------|
| document_id | String | Reference to document |
| predicted_class | String | INVOICE, CONTRACT, REPORT, RESUME, OTHER |
| confidence | Float | Prediction confidence (0.0-1.0) |
| probabilities | Dict | All class probabilities |
| model_version | String | Model version used |
| latency_ms | Float | Inference latency |

### GenerativeResult Model

| Field | Type | Description |
|-------|------|-------------|
| document_id | String | Reference to document |
| summary | String | Generated summary (2-3 paragraphs) |
| questions | List[Dict] | Q&A pairs with question and answer |
| topics | List[String] | Extracted topics (up to 10) |
| action_items | List[String] | Identified action items |
| model_id | String | Bedrock model identifier |
| input_tokens | Integer | Tokens consumed |
| output_tokens | Integer | Tokens generated |

## Lambda Handlers

| Handler | Trigger | Purpose | Status Updates |
|---------|---------|---------|----------------|
| document_ingestion | S3 Event | Ingest uploaded documents | PENDING → INGESTED |
| text_extraction | Step Functions | Extract text via Textract | EXTRACTING → EXTRACTED |
| audio_transcription | Step Functions | Transcribe audio via Transcribe | EXTRACTING → EXTRACTED |
| content_analysis | Step Functions | Analyze via Comprehend/Rekognition | ANALYZING → ANALYZED |
| sagemaker_inference | Step Functions | Classify via SageMaker | CLASSIFYING → CLASSIFIED |
| bedrock_generation | Step Functions | Generate insights via Bedrock | GENERATING → (pending) |
| workflow_orchestration | Step Functions | Route, validate, aggregate, finalize | All transitions |
| training_pipeline | EventBridge | Manage SageMaker training | N/A |
| notification | SNS | Send notifications | N/A |

## Error Handling and Retry Strategy

### Retry Configuration by Service

| Service | Error Types | Retries | Initial Backoff | Multiplier |
|---------|-------------|---------|-----------------|------------|
| Textract | Throttling, ProvisionedThroughput | 3 | 30s | 2x |
| Transcribe | Throttling | 3 | 10s | 2x |
| Comprehend | Throttling | 3 | 10s | 2x |
| Rekognition | Throttling | 3 | 10s | 2x |
| SageMaker | Throttling | 3 | 5s | 2x |
| Bedrock | Throttling, ModelNotReady | 3 | 10s-30s | 2x |

### Exception Hierarchy

```
BaseException
├── ExtractionError (Textract failures)
├── TranscriptionError (Transcribe failures)
├── AnalysisError (Comprehend/Rekognition failures)
├── InferenceError (SageMaker failures)
├── GenerationError (Bedrock failures)
├── RetryableError (transient, includes retry_after_seconds)
└── NonRetryableError (permanent failures)
```

## Storage Structure

### S3 Buckets

```
s3://raw-bucket/
└── input/
    └── documents/
        ├── file1.pdf
        ├── file2.jpg
        └── audio.mp3

s3://processed-bucket/
└── {document_id}/
    ├── extraction.json
    ├── analysis.json
    ├── inference.json
    └── generation.json

s3://model-bucket/
├── training-data/
│   └── train.csv
├── model-artifacts/
│   └── {job_name}/
│       └── model.tar.gz
└── features/
```

### DynamoDB Table

**Primary Table: documents**
- Partition Key: `document_id`
- GSI: `status-index` (status as partition key)
- Billing: On-Demand

## Training Pipeline

### Training Job Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                      TRAINING PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   start_training                                                │
│     • Generate unique job_name (timestamp + uuid)               │
│     • Set hyperparameters (XGBoost):                            │
│       - max_depth: 5                                            │
│       - eta: 0.2                                                │
│       - num_class: 5                                            │
│       - num_round: 100                                          │
│     • Create training job on SageMaker                          │
│        │                                                        │
│        ▼                                                        │
│   check_status                                                  │
│     • Poll: Completed | InProgress | Failed                     │
│     • On Completed: notify_training_complete                    │
│     • On Failed: notify_alert (TrainingFailed)                  │
│        │                                                        │
│        ▼                                                        │
│   register_model                                                │
│     • Create model package in Model Registry                    │
│     • Set approval: PendingManualApproval                       │
│        │                                                        │
│        ▼                                                        │
│   deploy_model                                                  │
│     • Create SageMaker model from artifacts                     │
│     • Create endpoint configuration                             │
│     • Update endpoint (blue/green deployment)                   │
│     • Notify ModelDeployed alert                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Monitoring and Observability

### CloudWatch Metrics

- Lambda invocations and duration per function
- Step Functions execution success/failure rates
- Service throttling and failure events
- Processing times by stage
- Bedrock token usage (input/output)

### Logging

- AWS Lambda Powertools structured JSON logging
- X-Ray distributed tracing
- Document context (document_id) in all logs
- Step Functions execution history

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| AWS_REGION | AWS region (default: eu-central-2) |
| RAW_BUCKET | S3 bucket for raw documents |
| PROCESSED_BUCKET | S3 bucket for results |
| MODEL_BUCKET | S3 bucket for ML models |
| DOCUMENTS_TABLE | DynamoDB table name |
| WORKFLOW_ARN | Step Functions state machine ARN |
| SAGEMAKER_ENDPOINT_NAME | SageMaker inference endpoint |
| BEDROCK_MODEL_ID | Bedrock model (Claude 3 Sonnet) |
| BEDROCK_MAX_TOKENS | Max tokens for generation (4096) |
| ENABLE_PII_DETECTION | Enable PII detection (true/false) |
| ENABLE_MODERATION | Enable content moderation (true/false) |

## Cost Optimization

| Strategy | Description |
|----------|-------------|
| Textract API Selection | Sync for <5MB, async for larger files |
| Lambda Memory | Optimized 128-1024MB based on workload |
| SageMaker Endpoints | On-demand with configurable instances |
| Bedrock Tokens | Track input/output for cost monitoring |
| S3 Lifecycle | Transition old documents to cheaper tiers |
| DynamoDB | On-demand billing for variable workloads |
