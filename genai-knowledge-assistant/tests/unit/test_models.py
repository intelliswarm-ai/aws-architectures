"""Unit tests for data models."""

import pytest
from pydantic import ValidationError

from src.common.models import (
    Document,
    DocumentMetadata,
    DocumentStatus,
    QueryRequest,
    QueryResponse,
    QueryType,
    RetrievalResult,
    SourceType,
)


class TestDocumentModels:
    """Tests for Document-related models."""

    def test_document_creation(self):
        """Test Document model creation."""
        doc = Document(
            document_id="doc-123",
            knowledge_base_id="kb-456",
            source_type=SourceType.S3,
            source_uri="s3://bucket/key.txt",
        )

        assert doc.document_id == "doc-123"
        assert doc.knowledge_base_id == "kb-456"
        assert doc.source_type == SourceType.S3
        assert doc.status == DocumentStatus.PENDING

    def test_document_with_metadata(self):
        """Test Document with metadata."""
        metadata = DocumentMetadata(
            title="Test Document",
            author="Test Author",
            tags=["test", "sample"],
        )

        doc = Document(
            document_id="doc-123",
            knowledge_base_id="kb-456",
            source_type=SourceType.S3,
            source_uri="s3://bucket/key.txt",
            metadata=metadata,
        )

        assert doc.metadata.title == "Test Document"
        assert doc.metadata.author == "Test Author"
        assert "test" in doc.metadata.tags

    def test_document_status_enum(self):
        """Test DocumentStatus enum values."""
        assert DocumentStatus.PENDING.value == "pending"
        assert DocumentStatus.PROCESSING.value == "processing"
        assert DocumentStatus.INDEXED.value == "indexed"
        assert DocumentStatus.FAILED.value == "failed"

    def test_source_type_enum(self):
        """Test SourceType enum values."""
        assert SourceType.S3.value == "s3"
        assert SourceType.URL.value == "url"
        assert SourceType.API.value == "api"
        assert SourceType.UPLOAD.value == "upload"


class TestQueryModels:
    """Tests for Query-related models."""

    def test_query_request_creation(self):
        """Test QueryRequest model creation."""
        request = QueryRequest(query="What is AI?")

        assert request.query == "What is AI?"
        assert request.top_k == 5
        assert request.score_threshold == 0.0
        assert request.generate_response is True

    def test_query_request_with_options(self):
        """Test QueryRequest with custom options."""
        request = QueryRequest(
            query="What is machine learning?",
            knowledge_base_id="kb-123",
            query_type=QueryType.HYBRID,
            top_k=10,
            score_threshold=0.8,
            generate_response=False,
        )

        assert request.query_type == QueryType.HYBRID
        assert request.top_k == 10
        assert request.score_threshold == 0.8
        assert request.generate_response is False

    def test_query_request_validation(self):
        """Test QueryRequest validation."""
        with pytest.raises(ValidationError):
            QueryRequest(query="")  # Empty query should fail

    def test_query_request_top_k_bounds(self):
        """Test QueryRequest top_k bounds."""
        with pytest.raises(ValidationError):
            QueryRequest(query="test", top_k=0)  # Below minimum

        with pytest.raises(ValidationError):
            QueryRequest(query="test", top_k=25)  # Above maximum

    def test_query_response_creation(self):
        """Test QueryResponse model creation."""
        response = QueryResponse(
            query_id="q-123",
            query="What is AI?",
            answer="AI is artificial intelligence.",
            sources=[],
            tokens_used=150,
            latency_ms=500,
        )

        assert response.query_id == "q-123"
        assert response.answer == "AI is artificial intelligence."
        assert response.tokens_used == 150

    def test_retrieval_result_creation(self):
        """Test RetrievalResult model creation."""
        result = RetrievalResult(
            chunk_id="chunk-123",
            document_id="doc-456",
            content="This is the content.",
            score=0.95,
            source_uri="s3://bucket/doc.txt",
        )

        assert result.chunk_id == "chunk-123"
        assert result.score == 0.95
        assert result.content == "This is the content."


class TestModelSerialization:
    """Tests for model serialization."""

    def test_document_to_dict(self):
        """Test Document serialization to dict."""
        doc = Document(
            document_id="doc-123",
            knowledge_base_id="kb-456",
            source_type=SourceType.S3,
            source_uri="s3://bucket/key.txt",
        )

        data = doc.model_dump(by_alias=True)

        assert data["documentId"] == "doc-123"
        assert data["knowledgeBaseId"] == "kb-456"
        assert data["sourceType"] == "s3"

    def test_query_request_from_dict(self):
        """Test QueryRequest creation from dict."""
        data = {
            "query": "What is AI?",
            "topK": 10,
            "scoreThreshold": 0.5,
            "generateResponse": True,
        }

        request = QueryRequest(**data)

        assert request.query == "What is AI?"
        assert request.top_k == 10

    def test_query_response_json(self):
        """Test QueryResponse JSON serialization."""
        response = QueryResponse(
            query_id="q-123",
            query="Test query",
            answer="Test answer",
            sources=[
                RetrievalResult(
                    chunk_id="c-1",
                    document_id="d-1",
                    content="Content",
                    score=0.9,
                )
            ],
        )

        json_str = response.model_dump_json(by_alias=True)

        assert "queryId" in json_str
        assert "q-123" in json_str
