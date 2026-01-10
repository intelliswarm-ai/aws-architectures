# Business Logic - GenAI Knowledge Assistant

## Overview

The GenAI Knowledge Assistant is a RAG (Retrieval-Augmented Generation) system that enables enterprises to build intelligent Q&A systems over their document collections. It combines Amazon Bedrock's foundation models with Knowledge Bases and Agents for accurate, grounded responses.

## Core Components

### 1. Document Ingestion Pipeline

```
Document Upload → S3 → Lambda Trigger → Chunking → Embedding → Vector Store
```

#### Process Flow
1. **Document Upload**: Users upload documents to S3 bucket under `documents/` prefix
2. **S3 Event Trigger**: Lambda function triggered on `s3:ObjectCreated:*`
3. **Text Extraction**: Content extracted based on file type
4. **Chunking**: Documents split into chunks with configurable size and overlap
5. **Embedding Generation**: Titan Embeddings V2 generates 1024-dim vectors
6. **Vector Indexing**: Chunks indexed in OpenSearch Serverless

#### Chunking Strategy
- **Chunk Size**: 1000 characters (configurable)
- **Overlap**: 200 characters (20%)
- **Sentence Boundary**: Attempts to break at sentence boundaries
- **Metadata Preservation**: Document metadata attached to each chunk

### 2. Query Processing (RAG)

```
User Query → Embedding → Vector Search → Context Retrieval → LLM Generation → Response
```

#### Process Flow
1. **Query Embedding**: User query converted to vector using same embedding model
2. **Vector Search**: Semantic search in OpenSearch for top-K similar chunks
3. **Score Threshold**: Filter results below confidence threshold
4. **Context Assembly**: Retrieved chunks assembled into context
5. **Prompt Engineering**: Query + context formatted for Claude
6. **Response Generation**: Claude generates grounded response with citations

#### Retrieval Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `top_k` | 5 | Number of chunks to retrieve |
| `score_threshold` | 0.7 | Minimum similarity score |
| `generate_response` | true | Whether to generate LLM response |

### 3. Bedrock Knowledge Base Integration

For managed RAG, the system can use Bedrock Knowledge Bases:

#### Advantages
- Automatic document syncing from S3
- Managed vector store
- Built-in chunking and embedding
- Retrieve-and-generate in single API call

#### Sync Process
1. **Scheduled Sync**: Daily EventBridge trigger (configurable)
2. **On-Demand Sync**: API endpoint to trigger manual sync
3. **Incremental Updates**: Only new/modified documents processed

### 4. Bedrock Agent System

For complex, multi-step tasks:

```
User Input → Agent Reasoning → Tool Selection → Action Execution → Response
```

#### Agent Capabilities
- **Knowledge Retrieval**: Search the knowledge base
- **Session Memory**: Maintain conversation context
- **Multi-Turn**: Handle follow-up questions
- **Citations**: Provide source attribution

#### Agent Configuration
```python
instruction = """
You are a helpful knowledge assistant. Your role is to answer questions based on
the documents in the knowledge base. Follow these guidelines:

1. Base your answers on the information retrieved from the knowledge base
2. If you cannot find relevant information, say so clearly
3. Cite your sources when possible
4. Be concise but thorough in your responses
5. If asked about topics outside the knowledge base, politely redirect
"""
```

## API Endpoints

### POST /query

Query the knowledge base with RAG.

**Request:**
```json
{
  "query": "What is our return policy?",
  "knowledgeBaseId": "optional-kb-id",
  "queryType": "semantic",
  "topK": 5,
  "scoreThreshold": 0.7,
  "generateResponse": true,
  "filters": {
    "tags": ["policy"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "queryId": "q-123",
    "query": "What is our return policy?",
    "answer": "Our return policy allows returns within 30 days...",
    "sources": [
      {
        "chunkId": "chunk-1",
        "documentId": "doc-abc",
        "content": "Return Policy: Customers may return...",
        "score": 0.95,
        "sourceUri": "s3://bucket/policies/return.pdf"
      }
    ],
    "tokensUsed": 350,
    "latencyMs": 1200,
    "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0"
  }
}
```

### POST /documents

Ingest a new document.

**Request:**
```json
{
  "sourceUri": "s3://bucket/documents/handbook.pdf",
  "sourceType": "s3",
  "knowledgeBaseId": "optional-kb-id",
  "metadata": {
    "title": "Employee Handbook",
    "author": "HR Department",
    "tags": ["hr", "policy", "handbook"]
  },
  "sync": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "documentId": "doc-abc123",
    "status": "processing",
    "message": "Document queued for processing"
  }
}
```

### POST /agent

Interact with Bedrock Agent.

**Request:**
```json
{
  "inputText": "Find information about vacation policy and summarize key points",
  "sessionId": "session-123",
  "enableTrace": false,
  "sessionAttributes": {
    "userId": "user-456"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sessionId": "session-123",
    "outputText": "Based on the employee handbook, here are the key points about vacation policy...",
    "citations": [
      {
        "chunkId": "chunk-5",
        "documentId": "doc-handbook",
        "content": "Vacation Policy: All full-time employees...",
        "score": 0.92,
        "sourceUri": "s3://bucket/handbook.pdf"
      }
    ],
    "actions": [
      {
        "actionType": "search",
        "actionGroup": "KnowledgeBase",
        "functionName": "retrieve",
        "parameters": {"query": "vacation policy"}
      }
    ]
  }
}
```

## Data Models

### Document
```python
class Document:
    document_id: str
    knowledge_base_id: str
    source_type: SourceType  # s3, url, api, upload
    source_uri: str
    status: DocumentStatus   # pending, processing, indexed, failed
    metadata: DocumentMetadata
    chunk_count: int
    indexed_at: datetime
    created_at: datetime
    updated_at: datetime
```

### DocumentChunk
```python
class DocumentChunk:
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    start_offset: int
    end_offset: int
    embedding: list[float]  # 1024 dimensions
    metadata: dict
```

### QueryRequest
```python
class QueryRequest:
    query: str
    knowledge_base_id: str | None
    query_type: QueryType  # semantic, hybrid, keyword
    top_k: int = 5
    score_threshold: float = 0.7
    filters: dict
    generate_response: bool = True
    conversation_id: str | None
```

## Error Handling

### Retryable Errors
- `ServiceUnavailableError`: Transient AWS service issues
- `ThrottlingError`: Rate limit exceeded
- `DatabaseError`: DynamoDB transient errors
- `OpenSearchError`: Vector store transient errors

### Non-Retryable Errors
- `ValidationError`: Invalid input
- `ResourceNotFoundError`: Document/KB not found
- `ConfigurationError`: Missing configuration
- `ContentFilterError`: Content blocked by guardrails

### Error Response Format
```json
{
  "success": false,
  "error": "Document not found",
  "errorCode": "RESOURCE_NOT_FOUND",
  "details": {
    "resourceType": "Document",
    "resourceId": "doc-123"
  }
}
```

## Security Considerations

### IAM Permissions
- Lambda roles follow least privilege
- Bedrock model access restricted to specific models
- S3 access limited to documents bucket
- DynamoDB access limited to specific tables

### Data Protection
- All S3 objects encrypted (AES-256)
- DynamoDB encryption enabled
- OpenSearch encryption at rest
- TLS for all API communications

### Content Safety
- Bedrock guardrails for content filtering
- Input validation on all endpoints
- Query length limits enforced
- Rate limiting at API Gateway

## Observability

### Logging
- Lambda Powertools structured logging
- Request/response logging (sanitized)
- Error tracking with stack traces
- Correlation IDs across services

### Metrics
- Query count and latency
- Token usage
- Document ingestion rate
- Error rates by type

### Tracing
- X-Ray tracing enabled
- End-to-end request tracing
- Service map visualization
- Performance bottleneck identification

## Performance Optimization

### Lambda
- Connection reuse with `@lru_cache`
- Optimized client configurations
- Right-sized memory allocation
- Cold start minimization

### Vector Search
- Approximate nearest neighbor (HNSW)
- Configurable ef_search parameter
- Index optimization for query patterns

### Caching Strategies
- DynamoDB DAX for hot paths (optional)
- API Gateway caching for static content
- Lambda execution context reuse
