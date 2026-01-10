"""Pytest configuration and fixtures."""

import os
from unittest.mock import MagicMock, patch

import pytest


# Set environment variables before importing application code
@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Set up environment variables for testing."""
    os.environ.update({
        "AWS_REGION": "us-east-1",
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "DEBUG",
        "POWERTOOLS_SERVICE_NAME": "genai-assistant-test",
        "POWERTOOLS_METRICS_NAMESPACE": "GenAIKnowledgeAssistant/Test",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "BEDROCK_EMBEDDING_MODEL_ID": "amazon.titan-embed-text-v2:0",
        "DOCUMENTS_BUCKET": "test-documents-bucket",
        "DOCUMENTS_TABLE": "test-documents-table",
        "CONVERSATIONS_TABLE": "test-conversations-table",
        "OPENSEARCH_COLLECTION_ENDPOINT": "test.us-east-1.aoss.amazonaws.com",
        "OPENSEARCH_INDEX_NAME": "test-index",
        "OPENSEARCH_VECTOR_DIMENSION": "1024",
        "KNOWLEDGE_BASE_ID": "test-kb-id",
    })


@pytest.fixture
def mock_bedrock_runtime():
    """Mock Bedrock Runtime client."""
    with patch("src.common.clients.get_bedrock_runtime_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_bedrock_agent_runtime():
    """Mock Bedrock Agent Runtime client."""
    with patch("src.common.clients.get_bedrock_agent_runtime_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB resource."""
    with patch("src.common.clients.get_dynamodb_resource") as mock:
        resource = MagicMock()
        mock.return_value = resource
        yield resource


@pytest.fixture
def mock_s3():
    """Mock S3 client."""
    with patch("src.common.clients.get_s3_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "documentId": "test-doc-123",
        "knowledgeBaseId": "test-kb-id",
        "sourceType": "s3",
        "sourceUri": "s3://test-bucket/test-doc.txt",
        "status": "indexed",
        "metadata": {
            "title": "Test Document",
            "author": "Test Author",
        },
        "chunkCount": 5,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_query_request():
    """Sample query request for testing."""
    return {
        "query": "What is the capital of France?",
        "topK": 5,
        "scoreThreshold": 0.7,
        "generateResponse": True,
    }


@pytest.fixture
def sample_embedding():
    """Sample embedding vector for testing."""
    return [0.1] * 1024  # 1024-dimensional vector


@pytest.fixture
def lambda_context():
    """Mock Lambda context."""
    context = MagicMock()
    context.function_name = "test-function"
    context.memory_limit_in_mb = 512
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
    context.aws_request_id = "test-request-id"
    context.get_remaining_time_in_millis.return_value = 60000
    return context
