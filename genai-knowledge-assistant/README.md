# GenAI Knowledge Assistant

**RAG-Powered Enterprise Knowledge Management** - A serverless knowledge assistant using Amazon Bedrock, Knowledge Bases, and Agents for intelligent document Q&A.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GenAI Knowledge Assistant                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  Users   │───▶│  API Gateway    │──▶│  Lambda Handlers                 │ │
│  └──────────┘    │  (REST API)     │    │  - API Handler                  │ │
│                  └─────────────────┘    │  - Query Handler                │ │
│                                         │  - Ingestion Handler            │ │
│                                         │  - Agent Handler                │ │
│                                         │  - Sync Handler                 │ │
│                                         └───────────┬─────────────────────┘ │
│                                                     │                       │
│  ┌──────────────────────────────────────────────────┼────────────────────┐  │
│  │                         Services Layer           │                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┴───────┐            │  │
│  │  │  Bedrock    │  │  Knowledge  │  │   OpenSearch        │            │  │
│  │  │  Service    │  │  Base Svc   │  │   Serverless        │            │  │
│  │  │  (Claude)   │  │  (RAG)      │  │   (Vector Store)    │            │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘            │  │
│  │         │                │                    │                       │  │
│  │  ┌──────▼────────────────▼────────────────────▼──────────────────┐    │  │
│  │  │                     Amazon Bedrock                            │    │  │
│  │  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐  │    │  │
│  │  │  │ Claude 3.5    │  │ Titan         │  │ Knowledge Base    │  │    │  │
│  │  │  │ Sonnet        │  │ Embeddings    │  │ + Agent           │  │    │  │
│  │  │  └───────────────┘  └───────────────┘  └───────────────────┘  │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         Storage Layer                                  │ │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────────┐   │ │
│  │  │  S3           │  │  DynamoDB     │  │  OpenSearch Serverless    │   │ │
│  │  │  (Documents)  │  │  (Metadata)   │  │  (Vector Index)           │   │ │
│  │  └───────────────┘  └───────────────┘  └───────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Features

### Core Capabilities
- **RAG Pipeline** - Retrieval-Augmented Generation for accurate, grounded answers
- **Bedrock Knowledge Bases** - Managed document ingestion and retrieval
- **Bedrock Agents** - Autonomous agents with tool use and multi-turn conversations
- **OpenSearch Serverless** - Scalable vector store for semantic search
- **Document Processing** - Automatic chunking, embedding, and indexing

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/query` | POST | Query the knowledge base |
| `/documents` | GET/POST | List or ingest documents |
| `/documents/{id}` | GET/DELETE | Get or delete document |
| `/agent` | POST | Interact with Bedrock Agent |
| `/knowledge-bases` | GET | List knowledge bases |
| `/knowledge-bases/{id}/sync` | POST | Trigger sync |

### Tech Stack
- **Runtime**: Python 3.12
- **AI/ML**: Amazon Bedrock (Claude 3.5 Sonnet, Titan Embeddings)
- **Vector Store**: OpenSearch Serverless
- **IaC**: Terraform, CloudFormation, SAM
- **Observability**: AWS Lambda Powertools, X-Ray

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate credentials
- Python 3.12+
- Terraform 1.5+ or AWS SAM CLI

### Deploy with Terraform

```bash
cd genai-knowledge-assistant

# Build Lambda package
./scripts/build.sh

# Deploy infrastructure
./scripts/deploy.sh -e dev
```

### Deploy with SAM

```bash
cd genai-knowledge-assistant/sam

# Build and deploy
sam build
sam deploy --guided
```

## Project Structure

```
genai-knowledge-assistant/
├── src/
│   ├── common/              # Shared utilities
│   │   ├── config.py        # Pydantic settings
│   │   ├── models.py        # Data models
│   │   ├── exceptions.py    # Custom exceptions
│   │   └── clients.py       # AWS clients
│   ├── handlers/            # Lambda handlers
│   │   ├── api_handler.py   # REST API
│   │   ├── query_handler.py # RAG queries
│   │   ├── ingestion_handler.py
│   │   ├── agent_handler.py
│   │   └── sync_handler.py
│   └── services/            # Business logic
│       ├── bedrock_service.py
│       ├── embedding_service.py
│       ├── knowledge_base_service.py
│       ├── query_service.py
│       ├── document_service.py
│       └── agent_service.py
├── terraform/               # Terraform IaC
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
├── sam/                     # SAM templates
│   ├── template.yaml
│   └── samconfig.toml
├── scripts/                 # Build/deploy scripts
├── tests/                   # Unit/integration tests
└── docs/                    # Documentation
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BEDROCK_MODEL_ID` | Claude model ID | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `BEDROCK_EMBEDDING_MODEL_ID` | Embedding model | `amazon.titan-embed-text-v2:0` |
| `KNOWLEDGE_BASE_ID` | Bedrock KB ID | - |
| `OPENSEARCH_COLLECTION_ENDPOINT` | OpenSearch endpoint | - |
| `RETRIEVAL_TOP_K` | Number of results | `5` |
| `CHUNK_SIZE` | Document chunk size | `1000` |

### Terraform Variables

```hcl
# terraform.tfvars
project_name = "genai-assistant"
environment  = "dev"
aws_region   = "eu-central-2"

# Bedrock
bedrock_model_id           = "anthropic.claude-3-5-sonnet-20241022-v2:0"
enable_bedrock_agent       = true
create_knowledge_base      = true

# Vector Store
vector_dimension = 1024
chunk_size       = 1000
chunk_overlap    = 200
```

## Usage Examples

### Query the Knowledge Base

```bash
curl -X POST https://api-id.execute-api.region.amazonaws.com/dev/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is our refund policy?",
    "topK": 5,
    "generateResponse": true
  }'
```

### Ingest a Document

```bash
curl -X POST https://api-id.execute-api.region.amazonaws.com/dev/documents \
  -H "Content-Type: application/json" \
  -d '{
    "sourceUri": "s3://my-bucket/documents/policy.pdf",
    "sourceType": "s3",
    "metadata": {
      "title": "Refund Policy",
      "tags": ["policy", "refund"]
    }
  }'
```

### Interact with Agent

```bash
curl -X POST https://api-id.execute-api.region.amazonaws.com/dev/agent \
  -H "Content-Type: application/json" \
  -d '{
    "inputText": "Search for information about our product warranty and summarize it",
    "sessionId": "user-session-123"
  }'
```

## Testing

```bash
# Run all tests
./scripts/test.sh

# Unit tests only
./scripts/test.sh --unit

# With coverage
./scripts/test.sh --coverage
```

## Cost Considerations

| Service | Pricing |
|---------|---------|
| Bedrock Claude | $3.00 / 1M input tokens, $15.00 / 1M output tokens |
| Bedrock Titan Embeddings | $0.10 / 1M tokens |
| OpenSearch Serverless | ~$0.24/hr per OCU |
| Lambda | $0.20 / 1M requests |
| DynamoDB | Pay per request |
| S3 | $0.023/GB |

See [COST_SIMULATION.md](./docs/COST_SIMULATION.md) for detailed cost analysis.

## Documentation

- [Business Logic](./docs/BUSINESS_LOGIC.md) - Detailed system behavior
- [Cost Simulation](./docs/COST_SIMULATION.md) - Cost estimates and optimization
- [API Documentation](./docs/API.md) - Full API reference

## License

MIT License - See LICENSE file for details.
