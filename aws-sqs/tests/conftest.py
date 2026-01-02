"""Pytest configuration and fixtures."""

import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws

# Set environment variables before importing modules
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["TRANSACTION_QUEUE_URL"] = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
os.environ["TRANSACTIONS_TABLE_NAME"] = "test-transactions"
os.environ["IDEMPOTENCY_TABLE_NAME"] = "test-idempotency"


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def sqs_client(aws_credentials):
    """Create mocked SQS client."""
    with mock_aws():
        client = boto3.client("sqs", region_name="us-east-1")
        yield client


@pytest.fixture
def dynamodb_client(aws_credentials):
    """Create mocked DynamoDB client."""
    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        yield client


@pytest.fixture
def sqs_queue(sqs_client):
    """Create a test SQS queue."""
    response = sqs_client.create_queue(
        QueueName="test-transactions",
        Attributes={
            "VisibilityTimeout": "60",
            "MessageRetentionPeriod": "1209600",
        },
    )
    queue_url = response["QueueUrl"]
    os.environ["TRANSACTION_QUEUE_URL"] = queue_url
    return queue_url


@pytest.fixture
def dynamodb_tables(dynamodb_client):
    """Create test DynamoDB tables."""
    # Transactions table
    dynamodb_client.create_table(
        TableName="test-transactions",
        KeySchema=[{"AttributeName": "transaction_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "transaction_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    # Idempotency table
    dynamodb_client.create_table(
        TableName="test-idempotency",
        KeySchema=[{"AttributeName": "idempotency_key", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "idempotency_key", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    return {
        "transactions": "test-transactions",
        "idempotency": "test-idempotency",
    }


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for tests."""
    return {
        "transaction_type": "TRANSFER",
        "source_account": "1234567890",
        "target_account": "0987654321",
        "amount": Decimal("100.00"),
        "currency": "USD",
        "description": "Test transfer",
        "idempotency_key": "test-key-123",
    }


@pytest.fixture
def sample_sqs_message():
    """Sample SQS message for tests."""
    return {
        "MessageId": "test-message-id",
        "ReceiptHandle": "test-receipt-handle",
        "Body": '{"transaction_id": "test-txn-id", "transaction_type": "TRANSFER", "source_account": "1234567890", "target_account": "0987654321", "amount": "100.00", "currency": "USD", "idempotency_key": "test-key-123"}',
        "Attributes": {
            "ApproximateReceiveCount": "1",
            "SentTimestamp": "1640000000000",
            "ApproximateFirstReceiveTimestamp": "1640000001000",
        },
        "MessageAttributes": {
            "TransactionType": {"DataType": "String", "StringValue": "TRANSFER"},
            "Currency": {"DataType": "String", "StringValue": "USD"},
        },
    }
