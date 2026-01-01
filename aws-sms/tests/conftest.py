"""Pytest fixtures for SMS Marketing System tests."""

import os
import pytest
from unittest.mock import MagicMock, patch

import boto3
from moto import mock_aws


# Set environment variables before importing modules
os.environ["AWS_DEFAULT_REGION"] = "eu-central-2"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["STREAM_NAME"] = "test-sms-events"
os.environ["RESPONSES_TABLE"] = "test-responses"
os.environ["SUBSCRIBERS_TABLE"] = "test-subscribers"
os.environ["ARCHIVE_BUCKET"] = "test-archive"
os.environ["NOTIFICATIONS_TOPIC"] = "arn:aws:sns:eu-central-2:123456789012:test-topic"
os.environ["PINPOINT_APP_ID"] = "test-app-id"


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for testing."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-central-2"


@pytest.fixture
def kinesis_client(aws_credentials):
    """Create a mock Kinesis client."""
    with mock_aws():
        client = boto3.client("kinesis", region_name="eu-central-2")
        client.create_stream(
            StreamName="test-sms-events",
            ShardCount=1,
        )
        # Wait for stream to become active
        waiter = client.get_waiter("stream_exists")
        waiter.wait(StreamName="test-sms-events")
        yield client


@pytest.fixture
def dynamodb_client(aws_credentials):
    """Create a mock DynamoDB client with tables."""
    with mock_aws():
        client = boto3.client("dynamodb", region_name="eu-central-2")

        # Create responses table
        client.create_table(
            TableName="test-responses",
            KeySchema=[
                {"AttributeName": "subscriber_id", "KeyType": "HASH"},
                {"AttributeName": "response_timestamp", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "subscriber_id", "AttributeType": "S"},
                {"AttributeName": "response_timestamp", "AttributeType": "S"},
                {"AttributeName": "campaign_id", "AttributeType": "S"},
                {"AttributeName": "response_date", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "campaign-responses-index",
                    "KeySchema": [
                        {"AttributeName": "campaign_id", "KeyType": "HASH"},
                        {"AttributeName": "response_timestamp", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "date-responses-index",
                    "KeySchema": [
                        {"AttributeName": "response_date", "KeyType": "HASH"},
                        {"AttributeName": "response_timestamp", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create subscribers table
        client.create_table(
            TableName="test-subscribers",
            KeySchema=[
                {"AttributeName": "subscriber_id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "subscriber_id", "AttributeType": "S"},
                {"AttributeName": "phone_number", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "phone-number-index",
                    "KeySchema": [
                        {"AttributeName": "phone_number", "KeyType": "HASH"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield client


@pytest.fixture
def s3_client(aws_credentials):
    """Create a mock S3 client."""
    with mock_aws():
        client = boto3.client("s3", region_name="eu-central-2")
        client.create_bucket(
            Bucket="test-archive",
            CreateBucketConfiguration={"LocationConstraint": "eu-central-2"},
        )
        yield client


@pytest.fixture
def sns_client(aws_credentials):
    """Create a mock SNS client."""
    with mock_aws():
        client = boto3.client("sns", region_name="eu-central-2")
        client.create_topic(Name="test-topic")
        yield client


@pytest.fixture
def sample_sms_success_event():
    """Sample SMS success event from Pinpoint."""
    return {
        "event_type": "_SMS.SUCCESS",
        "event_timestamp": "2024-01-15T10:30:00.000Z",
        "arrival_timestamp": "2024-01-15T10:30:00.500Z",
        "application": {"app_id": "test-app-id"},
        "client": {"client_id": "user-123"},
        "attributes": {
            "message_id": "msg-456",
            "destination_phone_number": "+1234567890",
            "record_status": "DELIVERED",
            "iso_country_code": "US",
            "message_type": "PROMOTIONAL",
            "campaign_id": "camp-001",
            "journey_id": "journey-001",
        },
        "metrics": {"price_in_millicents_usd": 645},
    }


@pytest.fixture
def sample_inbound_sms_event():
    """Sample inbound SMS event."""
    return {
        "event_type": "_SMS.RECEIVED",
        "event_timestamp": "2024-01-15T10:35:00.000Z",
        "attributes": {
            "origination_number": "+1234567890",
            "destination_number": "+0987654321",
            "message_body": "YES",
            "keyword": "YES",
            "message_id": "inbound-123",
        },
    }


@pytest.fixture
def sample_opt_out_event():
    """Sample opt-out SMS event."""
    return {
        "event_type": "_SMS.RECEIVED",
        "event_timestamp": "2024-01-15T10:40:00.000Z",
        "attributes": {
            "origination_number": "+1234567890",
            "destination_number": "+0987654321",
            "message_body": "STOP",
            "keyword": "STOP",
            "message_id": "optout-123",
        },
    }


@pytest.fixture
def lambda_context():
    """Create a mock Lambda context."""
    context = MagicMock()
    context.function_name = "test-function"
    context.memory_limit_in_mb = 256
    context.invoked_function_arn = "arn:aws:lambda:eu-central-2:123456789012:function:test"
    context.aws_request_id = "test-request-id"
    return context
