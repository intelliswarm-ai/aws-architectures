"""Pytest configuration and fixtures for ML Canary Deployment tests."""

import os
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest

# Set test environment variables before importing modules
os.environ["AWS_REGION"] = "us-east-1"
os.environ["ENVIRONMENT"] = "test"
os.environ["SAGEMAKER_ENDPOINT_NAME"] = "test-endpoint"
os.environ["DEPLOYMENTS_TABLE"] = "test-deployments"
os.environ["METRICS_TABLE"] = "test-metrics"
os.environ["EVENTS_TABLE"] = "test-events"
os.environ["MODEL_ARTIFACTS_BUCKET"] = "test-models"
os.environ["INFERENCE_LOGS_BUCKET"] = "test-logs"
os.environ["ALERTS_TOPIC_ARN"] = "arn:aws:sns:us-east-1:123456789012:test-alerts"
os.environ["DEPLOYMENT_EVENTS_TOPIC_ARN"] = "arn:aws:sns:us-east-1:123456789012:test-events"


@pytest.fixture
def mock_aws_clients() -> Generator[MagicMock, None, None]:
    """Mock AWS clients for testing."""
    with patch("src.common.clients.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = MagicMock()
        yield mock_client


@pytest.fixture
def sample_inference_request() -> dict[str, Any]:
    """Sample inference request for testing."""
    return {
        "request_id": "req-test-123",
        "user_id": "user-456",
        "features": {
            "user_watch_time_30d": 1500.0,
            "user_sessions_30d": 45,
            "content_popularity_score": 0.85,
            "user_genre_affinity": 0.72,
        },
        "content_type": "application/json",
    }


@pytest.fixture
def sample_deployment_config() -> dict[str, Any]:
    """Sample deployment configuration for testing."""
    return {
        "endpoint_name": "test-endpoint",
        "current_variant": {
            "variant_name": "production",
            "model_name": "test-model-v1",
            "instance_type": "ml.m5.xlarge",
            "initial_instance_count": 1,
            "initial_weight": 0.9,
        },
        "canary_variant": {
            "variant_name": "canary",
            "model_name": "test-model-v2",
            "instance_type": "ml.m5.xlarge",
            "initial_instance_count": 1,
            "initial_weight": 0.1,
        },
        "auto_rollback_enabled": True,
        "latency_threshold_ms": 100.0,
        "error_rate_threshold": 0.01,
    }


@pytest.fixture
def sample_endpoint_metrics() -> dict[str, Any]:
    """Sample endpoint metrics for testing."""
    return {
        "invocation_count": 10000,
        "invocation_4xx_errors": 50,
        "invocation_5xx_errors": 10,
        "model_latency_p50_ms": 25.0,
        "model_latency_p90_ms": 45.0,
        "model_latency_p99_ms": 75.0,
        "cpu_utilization": 45.0,
        "memory_utilization": 60.0,
    }


@pytest.fixture
def api_gateway_event(sample_inference_request: dict[str, Any]) -> dict[str, Any]:
    """Sample API Gateway event for testing."""
    import json

    return {
        "requestContext": {
            "requestId": "test-request-id",
        },
        "body": json.dumps(sample_inference_request),
        "headers": {
            "Content-Type": "application/json",
        },
    }


@pytest.fixture
def lambda_context() -> MagicMock:
    """Mock Lambda context for testing."""
    context = MagicMock()
    context.function_name = "test-function"
    context.memory_limit_in_mb = 512
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
    context.aws_request_id = "test-request-id"
    return context
