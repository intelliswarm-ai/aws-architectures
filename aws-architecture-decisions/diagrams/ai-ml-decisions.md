# AI & ML Services Decision Tree

> **Purpose:** Choose the right AWS AI/ML service based on the task type, ML expertise level, and customization needs.

## AI Service Decision (No ML Expertise)

```mermaid
flowchart TD
    Start([AI/ML Task]) --> Q1{Task Type?}

    Q1 -->|Text analysis| Q2{Specific task?}
    Q1 -->|Document processing| TEXTRACT[Amazon Textract]
    Q1 -->|Image/Video| REKOGNITION[Amazon<br/>Rekognition]
    Q1 -->|Speech to text| TRANSCRIBE[Amazon<br/>Transcribe]
    Q1 -->|Text to speech| POLLY[Amazon Polly]
    Q1 -->|Translation| TRANSLATE[Amazon<br/>Translate]
    Q1 -->|Custom ML| SAGEMAKER[Amazon<br/>SageMaker]

    Q2 -->|Sentiment, entities| COMPREHEND[Amazon<br/>Comprehend]
    Q2 -->|Medical text| COMPREHEND_MED[Comprehend<br/>Medical]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px,color:#000000
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:#000000
    classDef start fill:#ADD8E6,stroke:#4169E1,stroke-width:2px,color:#000000
    class Start start

    class Start start
    class Q1,Q2 question
    class TEXTRACT,REKOGNITION,TRANSCRIBE,POLLY,TRANSLATE,SAGEMAKER,COMPREHEND,COMPREHEND_MED service
```

## Generative AI Decision

```mermaid
flowchart TD
    Start([Generative AI]) --> Q1{Use Case?}

    Q1 -->|Text generation| BEDROCK[Amazon Bedrock]
    Q1 -->|Knowledge base RAG| BEDROCK_KB[Bedrock<br/>Knowledge Bases]
    Q1 -->|Autonomous agents| BEDROCK_AG[Bedrock Agents]
    Q1 -->|Code generation| CODEWHISPERER[Amazon Q<br/>Developer]

    BEDROCK --> MODELS[Claude, Llama,<br/>Titan, etc.]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px,color:#000000
    classDef models fill:#E6E6FA,stroke:#9370DB,stroke-width:1px,color:#000000
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:#000000

    class Q1 question
    class BEDROCK,BEDROCK_KB,BEDROCK_AG,CODEWHISPERER service
    class MODELS models
```

## Data Preparation Decision

```mermaid
flowchart TD
    Start([Data Prep]) --> Q1{Coding preference?}

    Q1 -->|No-code| DATABREW[Glue DataBrew]
    Q1 -->|Code-based| GLUE[Glue ETL]
    Q1 -->|Big data/Spark| EMR[Amazon EMR]
    Q1 -->|Labeling| GROUNDTRUTH[SageMaker<br/>Ground Truth]

    DATABREW --> USE_DB[Visual profiling<br/>No coding required]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px,color:#000000
    classDef use fill:#E6E6FA,stroke:#9370DB,stroke-width:1px,color:#000000
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:#000000

    class Q1 question
    class DATABREW,GLUE,EMR,GROUNDTRUTH service
    class USE_DB use
```

## Keyword → Service Mapping

| Keywords / Signals | AWS Service | Reasoning |
|--------------------|-------------|-----------|
| sentiment, entities, key phrases | Comprehend | NLP without ML team |
| PDF, document extraction | Textract | OCR + form extraction |
| face detection, object detection | Rekognition | Computer vision |
| audio transcription | Transcribe | Speech to text |
| text to audio | Polly | Text to speech |
| language translation | Translate | Multi-language |
| custom ML model | SageMaker | Full ML lifecycle |
| no-code data prep | Glue DataBrew | Visual profiling |
| data labeling | SageMaker Ground Truth | Human + ML labeling |
| generative AI | Bedrock | Foundation models |
| RAG, knowledge search | Bedrock Knowledge Bases | Retrieval-augmented |

## Elimination Rules

| Never Choose | When | Because |
|--------------|------|---------|
| SageMaker | Simple NLP tasks | Use Comprehend instead |
| Custom ML | Pre-built API exists | Over-engineered |
| Rekognition | Document text | Use Textract for documents |
| Comprehend | Image analysis | Comprehend is text only |

## AI Services Comparison (No ML Required)

| Task | AWS Service | Input | Output |
|------|-------------|-------|--------|
| Text sentiment | Comprehend | Text | Sentiment score |
| Entity extraction | Comprehend | Text | Entities (people, places) |
| Document OCR | Textract | PDF/Image | Extracted text |
| Form extraction | Textract | Forms | Key-value pairs |
| Face detection | Rekognition | Image/Video | Face data |
| Object detection | Rekognition | Image/Video | Labels |
| Speech to text | Transcribe | Audio | Text transcript |
| Text to speech | Polly | Text | Audio |
| Translation | Translate | Text | Translated text |

## SageMaker Components

| Component | Purpose |
|-----------|---------|
| Studio | IDE for ML development |
| Training | Train custom models |
| Endpoints | Host models for inference |
| Pipelines | ML workflow automation |
| Ground Truth | Data labeling |
| Feature Store | Feature management |
| Model Registry | Model versioning |

## Bedrock vs SageMaker

| Aspect | Bedrock | SageMaker |
|--------|---------|-----------|
| Use Case | Foundation models, GenAI | Custom ML models |
| ML Expertise | Low | High |
| Customization | Fine-tuning | Full control |
| Models | Pre-trained (Claude, Llama, Titan) | Train your own |
| Pricing | Per token/request | Per compute time |

## Trade-off Matrix

| Service | ML Expertise | Customization | Time to Deploy |
|---------|--------------|---------------|----------------|
| Comprehend | None | Low | Minutes |
| Rekognition | None | Low | Minutes |
| Bedrock | Low | Medium | Hours |
| SageMaker | High | High | Days-Weeks |

## Real-World Scenarios

### Scenario 1: Customer Review Sentiment
**Requirement:** Analyze product review sentiment
**Decision:** Amazon Comprehend
**Reasoning:** Pre-built NLP, no ML expertise needed

### Scenario 2: Invoice Processing
**Requirement:** Extract data from scanned invoices
**Decision:** Amazon Textract
**Reasoning:** OCR + form extraction for documents

### Scenario 3: Content Moderation
**Requirement:** Detect inappropriate images
**Decision:** Amazon Rekognition
**Reasoning:** Pre-built content moderation

### Scenario 4: Call Center Transcription
**Requirement:** Transcribe customer calls
**Decision:** Amazon Transcribe
**Reasoning:** Speech to text with speaker diarization

### Scenario 5: Chatbot with Knowledge Base
**Requirement:** Build RAG-powered chatbot
**Decision:** Bedrock + Knowledge Bases
**Reasoning:** Foundation models + retrieval

### Scenario 6: Custom Fraud Detection
**Requirement:** Build custom fraud model
**Decision:** SageMaker
**Reasoning:** Need custom model training

### Scenario 7: No-Code Data Profiling
**Requirement:** Analysts need to clean data without coding
**Decision:** Glue DataBrew
**Reasoning:** Visual interface, no coding

## API Anomaly Detection

| Requirement | Solution |
|-------------|----------|
| Detect unusual API calls | CloudTrail + CloudWatch metric filter + alarm + SNS |
| Real-time threat detection | GuardDuty |

> **Rule:** API anomaly detection → CloudTrail + CloudWatch metric filter

## Common Mistakes

1. **Mistake:** Building custom NLP for sentiment
   **Correct approach:** Use Comprehend for standard NLP tasks

2. **Mistake:** Using Rekognition for document text
   **Correct approach:** Use Textract for document extraction

3. **Mistake:** SageMaker for simple classification
   **Correct approach:** Use pre-built AI services first

4. **Mistake:** Ignoring Bedrock for GenAI
   **Correct approach:** Bedrock provides managed foundation models

5. **Mistake:** Manual data labeling at scale
   **Correct approach:** Use SageMaker Ground Truth

## ML Pipeline Best Practices

| Stage | AWS Service |
|-------|-------------|
| Data Ingestion | S3, Kinesis |
| Data Prep | Glue, DataBrew |
| Feature Store | SageMaker Feature Store |
| Training | SageMaker Training |
| Validation | SageMaker Model Monitor |
| Deployment | SageMaker Endpoints |
| Monitoring | CloudWatch |

## Related Decisions

- [Analytics Decisions](./analytics-decisions.md) - Data preparation
- [Compute Decisions](./compute-decisions.md) - Training compute
- [Storage Decisions](./storage-decisions.md) - ML data storage

---

## Quick Reference

1. **Text NLP without ML** → Comprehend
2. **Document extraction** → Textract
3. **Image/video analysis** → Rekognition
4. **Speech to text** → Transcribe
5. **Text to speech** → Polly
6. **Translation** → Translate
7. **No-code data prep** → Glue DataBrew
8. **Custom ML models** → SageMaker
9. **Generative AI** → Bedrock
10. **RAG/Knowledge search** → Bedrock Knowledge Bases
11. **Data labeling** → SageMaker Ground Truth
12. **API anomaly detection** → CloudTrail + CloudWatch
