"""Pydantic models for document processing."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Document processing status."""

    PENDING = "PENDING"
    INGESTED = "INGESTED"
    EXTRACTING = "EXTRACTING"
    EXTRACTED = "EXTRACTED"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    CLASSIFYING = "CLASSIFYING"
    CLASSIFIED = "CLASSIFIED"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "PDF"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    TEXT = "TEXT"
    UNKNOWN = "UNKNOWN"


class Document(BaseModel):
    """Core document model."""

    document_id: str = Field(..., description="Unique document identifier")
    bucket: str = Field(..., description="S3 bucket name")
    key: str = Field(..., description="S3 object key")
    document_type: DocumentType = Field(default=DocumentType.UNKNOWN)
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    file_size: int | None = Field(default=None, description="File size in bytes")
    content_type: str | None = Field(default=None, description="MIME type")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = Field(default=None)
    retry_count: int = Field(default=0)

    class Config:
        use_enum_values = True


class ExtractionResult(BaseModel):
    """Result from text extraction (Textract/Transcribe)."""

    document_id: str
    extracted_text: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    language: str | None = Field(default=None)
    pages: int = Field(default=1)
    words: int = Field(default=0)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    forms: list[dict[str, Any]] = Field(default_factory=list)
    raw_response: dict[str, Any] = Field(default_factory=dict)


class EntityResult(BaseModel):
    """Entity extracted from text."""

    text: str
    entity_type: str
    score: float = Field(ge=0.0, le=1.0)
    begin_offset: int | None = None
    end_offset: int | None = None


class SentimentResult(BaseModel):
    """Sentiment analysis result."""

    sentiment: str  # POSITIVE, NEGATIVE, NEUTRAL, MIXED
    positive: float = Field(ge=0.0, le=1.0)
    negative: float = Field(ge=0.0, le=1.0)
    neutral: float = Field(ge=0.0, le=1.0)
    mixed: float = Field(ge=0.0, le=1.0)


class ImageLabel(BaseModel):
    """Label detected in an image."""

    name: str
    confidence: float = Field(ge=0.0, le=100.0)
    parents: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Result from content analysis (Comprehend/Rekognition)."""

    document_id: str
    entities: list[EntityResult] = Field(default_factory=list)
    key_phrases: list[str] = Field(default_factory=list)
    sentiment: SentimentResult | None = None
    language: str | None = None
    pii_entities: list[EntityResult] = Field(default_factory=list)
    image_labels: list[ImageLabel] = Field(default_factory=list)
    detected_text: list[str] = Field(default_factory=list)
    moderation_labels: list[dict[str, Any]] = Field(default_factory=list)


class InferenceResult(BaseModel):
    """Result from SageMaker inference."""

    document_id: str
    predicted_class: str
    confidence: float = Field(ge=0.0, le=1.0)
    probabilities: dict[str, float] = Field(default_factory=dict)
    model_version: str | None = None
    latency_ms: float | None = None


class GenerativeResult(BaseModel):
    """Result from Bedrock generation."""

    document_id: str
    summary: str = Field(default="")
    questions: list[dict[str, str]] = Field(default_factory=list)  # Q&A pairs
    topics: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    model_id: str | None = None
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)


class ProcessingResult(BaseModel):
    """Aggregated processing result."""

    document_id: str
    document: Document
    extraction: ExtractionResult | None = None
    analysis: AnalysisResult | None = None
    inference: InferenceResult | None = None
    generation: GenerativeResult | None = None
    processing_time_ms: float = Field(default=0.0)
    workflow_execution_id: str | None = None


class WorkflowInput(BaseModel):
    """Input to Step Functions workflow."""

    document_id: str
    bucket: str
    key: str
    document_type: DocumentType = DocumentType.UNKNOWN
    options: dict[str, Any] = Field(default_factory=dict)


class WorkflowOutput(BaseModel):
    """Output from Step Functions workflow."""

    document_id: str
    status: DocumentStatus
    result: ProcessingResult | None = None
    error: str | None = None
