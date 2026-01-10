"""Pydantic models for data validation and serialization."""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# =============================================================================
# Enums
# =============================================================================


class DocumentStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    DELETED = "deleted"


class SourceType(str, Enum):
    """Document source types."""

    S3 = "s3"
    URL = "url"
    API = "api"
    UPLOAD = "upload"


class EmbeddingModel(str, Enum):
    """Supported embedding models."""

    TITAN_V2 = "amazon.titan-embed-text-v2:0"
    TITAN_V1 = "amazon.titan-embed-text-v1"
    COHERE_ENGLISH = "cohere.embed-english-v3"
    COHERE_MULTILINGUAL = "cohere.embed-multilingual-v3"


class QueryType(str, Enum):
    """Query types for knowledge retrieval."""

    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    KEYWORD = "keyword"


class AgentActionType(str, Enum):
    """Agent action types."""

    RETRIEVE = "retrieve"
    GENERATE = "generate"
    SEARCH = "search"
    SUMMARIZE = "summarize"


# =============================================================================
# Document Models
# =============================================================================


class DocumentMetadata(BaseModel):
    """Metadata associated with a document."""

    model_config = ConfigDict(populate_by_name=True)

    title: str | None = None
    author: str | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")
    content_type: str | None = Field(default=None, alias="contentType")
    file_size: int | None = Field(default=None, alias="fileSize")
    language: str = "en"
    tags: list[str] = Field(default_factory=list)
    custom_attributes: dict[str, Any] = Field(
        default_factory=dict, alias="customAttributes"
    )


class Document(BaseModel):
    """Document model for knowledge base."""

    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(..., alias="documentId")
    knowledge_base_id: str = Field(..., alias="knowledgeBaseId")
    source_type: SourceType = Field(..., alias="sourceType")
    source_uri: str = Field(..., alias="sourceUri")
    status: DocumentStatus = DocumentStatus.PENDING
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    chunk_count: int = Field(default=0, alias="chunkCount")
    error_message: str | None = Field(default=None, alias="errorMessage")
    indexed_at: datetime | None = Field(default=None, alias="indexedAt")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")


class DocumentChunk(BaseModel):
    """A chunk of a document with embeddings."""

    model_config = ConfigDict(populate_by_name=True)

    chunk_id: str = Field(..., alias="chunkId")
    document_id: str = Field(..., alias="documentId")
    content: str
    chunk_index: int = Field(..., alias="chunkIndex")
    start_offset: int = Field(..., alias="startOffset")
    end_offset: int = Field(..., alias="endOffset")
    embedding: list[float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Knowledge Base Models
# =============================================================================


class KnowledgeBase(BaseModel):
    """Knowledge base configuration."""

    model_config = ConfigDict(populate_by_name=True)

    knowledge_base_id: str = Field(..., alias="knowledgeBaseId")
    name: str
    description: str | None = None
    embedding_model: EmbeddingModel = Field(
        default=EmbeddingModel.TITAN_V2, alias="embeddingModel"
    )
    vector_dimension: int = Field(default=1024, alias="vectorDimension")
    document_count: int = Field(default=0, alias="documentCount")
    status: str = "ACTIVE"
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")


# =============================================================================
# Query Models
# =============================================================================


class QueryRequest(BaseModel):
    """Request model for knowledge queries."""

    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(..., min_length=1, max_length=10000)
    knowledge_base_id: str | None = Field(default=None, alias="knowledgeBaseId")
    query_type: QueryType = Field(default=QueryType.SEMANTIC, alias="queryType")
    top_k: int = Field(default=5, ge=1, le=20, alias="topK")
    score_threshold: float = Field(
        default=0.0, ge=0.0, le=1.0, alias="scoreThreshold"
    )
    filters: dict[str, Any] = Field(default_factory=dict)
    include_metadata: bool = Field(default=True, alias="includeMetadata")
    generate_response: bool = Field(default=True, alias="generateResponse")
    conversation_id: str | None = Field(default=None, alias="conversationId")
    session_id: str | None = Field(default=None, alias="sessionId")


class RetrievalResult(BaseModel):
    """A single retrieval result from the knowledge base."""

    model_config = ConfigDict(populate_by_name=True)

    chunk_id: str = Field(..., alias="chunkId")
    document_id: str = Field(..., alias="documentId")
    content: str
    score: float = Field(..., ge=0.0, le=1.0)
    metadata: DocumentMetadata | None = None
    source_uri: str | None = Field(default=None, alias="sourceUri")


class QueryResponse(BaseModel):
    """Response model for knowledge queries."""

    model_config = ConfigDict(populate_by_name=True)

    query_id: str = Field(..., alias="queryId")
    query: str
    answer: str | None = None
    sources: list[RetrievalResult] = Field(default_factory=list)
    tokens_used: int = Field(default=0, alias="tokensUsed")
    latency_ms: int = Field(default=0, alias="latencyMs")
    model_id: str = Field(default="", alias="modelId")
    conversation_id: str | None = Field(default=None, alias="conversationId")


# =============================================================================
# Agent Models
# =============================================================================


class AgentRequest(BaseModel):
    """Request model for agent interactions."""

    model_config = ConfigDict(populate_by_name=True)

    input_text: str = Field(..., min_length=1, alias="inputText")
    session_id: str | None = Field(default=None, alias="sessionId")
    agent_id: str | None = Field(default=None, alias="agentId")
    enable_trace: bool = Field(default=False, alias="enableTrace")
    session_attributes: dict[str, str] = Field(
        default_factory=dict, alias="sessionAttributes"
    )
    prompt_session_attributes: dict[str, str] = Field(
        default_factory=dict, alias="promptSessionAttributes"
    )


class AgentAction(BaseModel):
    """An action taken by the agent."""

    model_config = ConfigDict(populate_by_name=True)

    action_type: AgentActionType = Field(..., alias="actionType")
    action_group: str = Field(..., alias="actionGroup")
    function_name: str = Field(..., alias="functionName")
    parameters: dict[str, Any] = Field(default_factory=dict)
    result: str | None = None


class AgentResponse(BaseModel):
    """Response model for agent interactions."""

    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., alias="sessionId")
    output_text: str = Field(..., alias="outputText")
    citations: list[RetrievalResult] = Field(default_factory=list)
    actions: list[AgentAction] = Field(default_factory=list)
    trace: dict[str, Any] | None = None


# =============================================================================
# Conversation Models
# =============================================================================


class ConversationMessage(BaseModel):
    """A message in a conversation."""

    model_config = ConfigDict(populate_by_name=True)

    message_id: str = Field(..., alias="messageId")
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    """A conversation with history."""

    model_config = ConfigDict(populate_by_name=True)

    conversation_id: str = Field(..., alias="conversationId")
    session_id: str = Field(..., alias="sessionId")
    user_id: str | None = Field(default=None, alias="userId")
    messages: list[ConversationMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    ttl: int | None = None  # DynamoDB TTL


# =============================================================================
# API Response Models
# =============================================================================


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""

    success: bool = True
    data: T | None = None
    error: str | None = None
    error_code: str | None = Field(default=None, alias="errorCode")
    request_id: str | None = Field(default=None, alias="requestId")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[T]
    total: int
    page: int = 1
    page_size: int = Field(default=20, alias="pageSize")
    has_more: bool = Field(default=False, alias="hasMore")
    next_token: str | None = Field(default=None, alias="nextToken")


# =============================================================================
# Ingestion Models
# =============================================================================


class IngestionRequest(BaseModel):
    """Request to ingest a document."""

    model_config = ConfigDict(populate_by_name=True)

    source_uri: str = Field(..., alias="sourceUri")
    source_type: SourceType = Field(default=SourceType.S3, alias="sourceType")
    knowledge_base_id: str | None = Field(default=None, alias="knowledgeBaseId")
    metadata: DocumentMetadata | None = None
    sync: bool = False  # Synchronous processing


class IngestionResponse(BaseModel):
    """Response from document ingestion."""

    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(..., alias="documentId")
    status: DocumentStatus
    message: str
