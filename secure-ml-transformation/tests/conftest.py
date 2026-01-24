"""Pytest fixtures and configuration."""

import os
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def set_test_environment():
    """Set test environment variables."""
    env_vars = {
        "AWS_REGION": "eu-central-2",
        "ENVIRONMENT": "test",
        "PROJECT_NAME": "secure-ml-transform",
        "RAW_DATA_BUCKET": "test-raw-bucket",
        "PROCESSED_DATA_BUCKET": "test-processed-bucket",
        "KMS_KEY_ID": "test-key-id",
        "LOG_LEVEL": "DEBUG",
    }

    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture
def sample_transaction():
    """Sample transaction record for testing."""
    return {
        "transaction_id": "txn_001",
        "customer_id": "cust_12345",
        "account_number": "1234567890",
        "card_number": "4532-1234-5678-9012",
        "email": "test@example.com",
        "phone": "+41791234567",
        "transaction_amount": Decimal("150.00"),
        "currency": "CHF",
        "merchant_category_code": "5411",
        "merchant_name": "Test Grocery Store",
        "transaction_timestamp": datetime(2024, 1, 15, 10, 30, 0),
        "location_country": "CH",
        "location_city": "Zurich",
    }


@pytest.fixture
def sample_transactions(sample_transaction):
    """List of sample transactions for testing."""
    transactions = []
    for i in range(10):
        txn = sample_transaction.copy()
        txn["transaction_id"] = f"txn_{i:03d}"
        txn["customer_id"] = f"cust_{10000 + i}"
        txn["transaction_amount"] = Decimal(str(100 + i * 50))
        transactions.append(txn)
    return transactions


@pytest.fixture
def pii_config():
    """Sample PII tokenization configuration."""
    return [
        {
            "column_name": "customer_id",
            "method": "deterministic",
            "output_length": 16,
        },
        {
            "column_name": "card_number",
            "method": "format_preserving",
            "preserve_prefix": 4,
            "preserve_suffix": 4,
        },
        {
            "column_name": "email",
            "method": "hash",
        },
    ]


@pytest.fixture
def binning_config():
    """Sample binning configuration."""
    return {
        "method": "percentile",
        "column": "transaction_amount",
        "percentiles": [0, 10, 25, 50, 75, 90, 95, 99, 100],
        "labels": ["micro", "small", "low", "medium", "high", "large", "very_large", "extreme"],
    }


@pytest.fixture
def merchant_mapping():
    """Sample merchant category mapping."""
    return {
        "5411": {
            "category": "grocery_stores",
            "category_id": 1,
            "risk_level": "low",
            "risk_score": 0.1,
            "parent_category": "retail",
            "is_cash_equivalent": False,
        },
        "5812": {
            "category": "restaurants",
            "category_id": 2,
            "risk_level": "medium",
            "risk_score": 0.3,
            "parent_category": "dining",
            "is_cash_equivalent": False,
        },
        "6011": {
            "category": "atm",
            "category_id": 3,
            "risk_level": "high",
            "risk_score": 0.7,
            "parent_category": "financial",
            "is_cash_equivalent": True,
        },
    }


@pytest.fixture
def mock_glue_client():
    """Mock Glue client."""
    client = MagicMock()
    client.start_job_run.return_value = {"JobRunId": "jr_test_123"}
    client.get_job_run.return_value = {
        "JobRun": {
            "Id": "jr_test_123",
            "JobName": "test-job",
            "State": "SUCCEEDED",
            "ExecutionTime": 300,
        }
    }
    return client


@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_cloudwatch_client():
    """Mock CloudWatch Logs client."""
    client = MagicMock()
    return client


@pytest.fixture
def lambda_context():
    """Mock Lambda context."""
    context = MagicMock()
    context.function_name = "test-function"
    context.memory_limit_in_mb = 256
    context.invoked_function_arn = "arn:aws:lambda:eu-central-2:123456789012:function:test"
    context.aws_request_id = "test-request-id"
    return context
