"""Unit tests for custom exceptions."""

import pytest

from src.common.exceptions import (
    AgentError,
    AuthenticationError,
    AuthorizationError,
    BaseError,
    BedrockThrottlingError,
    ConfigurationError,
    ContentFilterError,
    DatabaseError,
    DocumentIngestionError,
    EmbeddingError,
    KnowledgeBaseError,
    NonRetryableError,
    OpenSearchError,
    QueryError,
    ResourceNotFoundError,
    RetryableError,
    ServiceUnavailableError,
    ThrottlingError,
    ValidationError,
)


class TestBaseError:
    """Tests for BaseError."""

    def test_base_error_creation(self):
        """Test BaseError creation."""
        error = BaseError("Test error", error_code="TEST_ERROR")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"

    def test_base_error_to_dict(self):
        """Test BaseError to_dict method."""
        error = BaseError(
            "Test error",
            error_code="TEST_ERROR",
            details={"field": "value"},
        )

        data = error.to_dict()

        assert data["error"] == "Test error"
        assert data["errorCode"] == "TEST_ERROR"
        assert data["details"]["field"] == "value"


class TestRetryableErrors:
    """Tests for retryable errors."""

    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError."""
        error = ServiceUnavailableError(
            message="Bedrock unavailable",
            service="bedrock",
            retry_after=60,
        )

        assert error.error_code == "SERVICE_UNAVAILABLE"
        assert error.retry_after == 60
        assert error.details["service"] == "bedrock"

    def test_throttling_error(self):
        """Test ThrottlingError."""
        error = ThrottlingError(service="bedrock", retry_after=30)

        assert error.error_code == "THROTTLING"
        assert error.retry_after == 30

    def test_bedrock_throttling_error(self):
        """Test BedrockThrottlingError."""
        error = BedrockThrottlingError(
            model_id="anthropic.claude-3-5-sonnet",
            retry_after=60,
        )

        assert error.error_code == "THROTTLING"
        assert error.details["modelId"] == "anthropic.claude-3-5-sonnet"

    def test_database_error(self):
        """Test DatabaseError."""
        error = DatabaseError(
            message="DynamoDB error",
            table="documents",
            operation="put_item",
        )

        assert error.error_code == "DATABASE_ERROR"
        assert error.details["table"] == "documents"
        assert error.details["operation"] == "put_item"

    def test_opensearch_error(self):
        """Test OpenSearchError."""
        error = OpenSearchError(
            message="Index error",
            index="knowledge-index",
            operation="search",
        )

        assert error.error_code == "OPENSEARCH_ERROR"
        assert error.details["index"] == "knowledge-index"


class TestNonRetryableErrors:
    """Tests for non-retryable errors."""

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError(
            message="Invalid query",
            field="query",
            value="",
        )

        assert error.error_code == "VALIDATION_ERROR"
        assert error.details["field"] == "query"

    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError."""
        error = ResourceNotFoundError(
            message="Document not found",
            resource_type="Document",
            resource_id="doc-123",
        )

        assert error.error_code == "RESOURCE_NOT_FOUND"
        assert error.details["resourceType"] == "Document"
        assert error.details["resourceId"] == "doc-123"

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError(
            message="Missing config",
            config_key="BEDROCK_MODEL_ID",
        )

        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.details["configKey"] == "BEDROCK_MODEL_ID"

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError(message="Invalid token")

        assert error.error_code == "AUTHENTICATION_ERROR"
        assert error.message == "Invalid token"

    def test_authorization_error(self):
        """Test AuthorizationError."""
        error = AuthorizationError(
            message="Access denied",
            resource="document",
            action="delete",
        )

        assert error.error_code == "AUTHORIZATION_ERROR"
        assert error.details["resource"] == "document"


class TestKnowledgeBaseErrors:
    """Tests for knowledge base specific errors."""

    def test_knowledge_base_error(self):
        """Test KnowledgeBaseError."""
        error = KnowledgeBaseError(
            message="KB error",
            knowledge_base_id="kb-123",
            operation="retrieve",
        )

        assert error.error_code == "KNOWLEDGE_BASE_ERROR"
        assert error.details["knowledgeBaseId"] == "kb-123"

    def test_document_ingestion_error(self):
        """Test DocumentIngestionError."""
        error = DocumentIngestionError(
            message="Ingestion failed",
            document_id="doc-123",
            source_uri="s3://bucket/doc.txt",
            reason="Invalid format",
        )

        assert error.error_code == "DOCUMENT_INGESTION_ERROR"
        assert error.details["documentId"] == "doc-123"
        assert error.details["reason"] == "Invalid format"

    def test_embedding_error(self):
        """Test EmbeddingError."""
        error = EmbeddingError(
            message="Embedding failed",
            model_id="titan-embed",
            text_length=10000,
        )

        assert error.error_code == "EMBEDDING_ERROR"
        assert error.details["modelId"] == "titan-embed"
        assert error.details["textLength"] == 10000

    def test_query_error(self):
        """Test QueryError."""
        error = QueryError(
            message="Query failed",
            query="What is AI?",
            reason="timeout",
        )

        assert error.error_code == "QUERY_ERROR"
        assert error.details["reason"] == "timeout"

    def test_agent_error(self):
        """Test AgentError."""
        error = AgentError(
            message="Agent failed",
            agent_id="agent-123",
            session_id="session-456",
            reason="model_error",
        )

        assert error.error_code == "AGENT_ERROR"
        assert error.details["agentId"] == "agent-123"
        assert error.details["sessionId"] == "session-456"

    def test_content_filter_error(self):
        """Test ContentFilterError."""
        error = ContentFilterError(
            message="Content blocked",
            filter_type="toxicity",
        )

        assert error.error_code == "CONTENT_FILTERED"
        assert error.details["filterType"] == "toxicity"


class TestErrorHierarchy:
    """Tests for error hierarchy."""

    def test_retryable_is_base_error(self):
        """Test RetryableError is BaseError."""
        error = RetryableError("Test")
        assert isinstance(error, BaseError)

    def test_non_retryable_is_base_error(self):
        """Test NonRetryableError is BaseError."""
        error = NonRetryableError("Test")
        assert isinstance(error, BaseError)

    def test_specific_errors_are_retryable(self):
        """Test specific errors inherit from RetryableError."""
        errors = [
            ServiceUnavailableError(),
            ThrottlingError(),
            DatabaseError(),
            OpenSearchError(),
        ]

        for error in errors:
            assert isinstance(error, RetryableError)

    def test_specific_errors_are_non_retryable(self):
        """Test specific errors inherit from NonRetryableError."""
        errors = [
            ValidationError(),
            ResourceNotFoundError(),
            ConfigurationError(),
            KnowledgeBaseError(),
            QueryError(),
            AgentError(),
        ]

        for error in errors:
            assert isinstance(error, NonRetryableError)
