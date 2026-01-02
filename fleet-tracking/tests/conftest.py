"""Pytest configuration and fixtures for GPS tracking tests."""

import os
from datetime import datetime
from unittest.mock import MagicMock

import boto3
import pytest
from moto import mock_aws

from src.common.models import EngineStatus, GPSCoordinate


@pytest.fixture(autouse=True)
def aws_credentials():
    """Set up mock AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-central-2"


@pytest.fixture(autouse=True)
def env_setup():
    """Set up environment variables for tests."""
    os.environ["STREAM_NAME"] = "test-gps-stream"
    os.environ["DYNAMODB_TABLE"] = "test-truck-positions"
    os.environ["GEOFENCES_TABLE"] = "test-geofences"
    os.environ["S3_BUCKET"] = "test-gps-archive"
    os.environ["SNS_TOPIC_ARN"] = "arn:aws:sns:eu-central-2:123456789012:test-alerts"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["ENVIRONMENT"] = "test"


@pytest.fixture
def sample_gps_coordinate():
    """Create a sample GPS coordinate."""
    return GPSCoordinate(
        truck_id="TRK-001",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        latitude=47.3769,
        longitude=8.5417,
        speed_kmh=45.5,
        heading=180,
        altitude_m=408,
        accuracy_m=5,
        fuel_level_pct=75,
        engine_status=EngineStatus.RUNNING,
    )


@pytest.fixture
def sample_gps_coordinates():
    """Create a list of sample GPS coordinates."""
    base_lat = 47.3769
    base_lon = 8.5417

    coordinates = []
    for i in range(10):
        coord = GPSCoordinate(
            truck_id=f"TRK-{i % 3 + 1:03d}",
            timestamp=datetime(2024, 1, 15, 10, 30, i),
            latitude=base_lat + (i * 0.001),
            longitude=base_lon + (i * 0.001),
            speed_kmh=40 + i,
            heading=(180 + i * 10) % 360,
            altitude_m=400 + i,
            accuracy_m=5,
            fuel_level_pct=75 - i,
            engine_status=EngineStatus.RUNNING if i % 3 != 0 else EngineStatus.IDLE,
        )
        coordinates.append(coord)

    return coordinates


@pytest.fixture
def mock_kinesis_client():
    """Create a mock Kinesis client."""
    with mock_aws():
        client = boto3.client("kinesis", region_name="eu-central-2")
        client.create_stream(StreamName="test-gps-stream", ShardCount=1)
        # Wait for stream to become active (moto simulates this)
        yield client


@pytest.fixture
def mock_dynamodb_client():
    """Create a mock DynamoDB client with tables."""
    with mock_aws():
        client = boto3.client("dynamodb", region_name="eu-central-2")

        # Create positions table
        client.create_table(
            TableName="test-truck-positions",
            KeySchema=[{"AttributeName": "truck_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "truck_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create geofences table
        client.create_table(
            TableName="test-geofences",
            KeySchema=[{"AttributeName": "geofence_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "geofence_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        yield client


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client with bucket."""
    with mock_aws():
        client = boto3.client("s3", region_name="eu-central-2")
        client.create_bucket(
            Bucket="test-gps-archive",
            CreateBucketConfiguration={"LocationConstraint": "eu-central-2"},
        )
        yield client


@pytest.fixture
def mock_sns_client():
    """Create a mock SNS client with topic."""
    with mock_aws():
        client = boto3.client("sns", region_name="eu-central-2")
        client.create_topic(Name="test-alerts")
        yield client


@pytest.fixture
def lambda_context():
    """Create a mock Lambda context."""
    context = MagicMock()
    context.function_name = "test-function"
    context.memory_limit_in_mb = 256
    context.invoked_function_arn = "arn:aws:lambda:eu-central-2:123456789012:function:test"
    context.aws_request_id = "test-request-id"
    context.get_remaining_time_in_millis = MagicMock(return_value=60000)
    return context
