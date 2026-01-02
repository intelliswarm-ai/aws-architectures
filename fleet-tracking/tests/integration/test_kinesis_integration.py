"""Integration tests for Kinesis service."""

import json
from datetime import datetime

import boto3
import pytest
from moto import mock_aws

from src.common.models import GPSCoordinate
from src.services.kinesis_service import KinesisService


@mock_aws
class TestKinesisIntegration:
    """Integration tests for Kinesis operations."""

    @pytest.fixture
    def kinesis_stream(self):
        """Create a mock Kinesis stream."""
        client = boto3.client("kinesis", region_name="eu-central-2")
        client.create_stream(
            StreamName="test-gps-stream",
            ShardCount=1,
        )
        # Wait for stream to be active
        waiter = client.get_waiter("stream_exists")
        waiter.wait(StreamName="test-gps-stream")
        return client

    def test_put_single_record(self, kinesis_stream):
        """Test putting a single record to Kinesis."""
        service = KinesisService(client=kinesis_stream)

        coord = GPSCoordinate(
            truck_id="TRK-001",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            latitude=47.3769,
            longitude=8.5417,
            speed_kmh=45.5,
        )

        response = service.put_record(coord)

        assert "ShardId" in response
        assert "SequenceNumber" in response

    def test_put_multiple_records(self, kinesis_stream):
        """Test putting multiple records to Kinesis."""
        service = KinesisService(client=kinesis_stream)

        coordinates = [
            GPSCoordinate(
                truck_id=f"TRK-{i:03d}",
                latitude=47.3769 + (i * 0.001),
                longitude=8.5417,
                speed_kmh=40 + i,
            )
            for i in range(10)
        ]

        result = service.put_records(coordinates)

        assert result["SuccessCount"] == 10
        assert result["FailureCount"] == 0

    def test_put_records_batch_handling(self, kinesis_stream):
        """Test batch handling for many records."""
        service = KinesisService(client=kinesis_stream)

        # Create more records than typical batch size
        coordinates = [
            GPSCoordinate(
                truck_id=f"TRK-{i:03d}",
                latitude=47.0 + (i * 0.001),
                longitude=8.0,
                speed_kmh=50,
            )
            for i in range(50)
        ]

        result = service.put_records(coordinates)

        assert result["SuccessCount"] == 50
        assert result["FailureCount"] == 0

    def test_parse_kinesis_records(self, kinesis_stream):
        """Test parsing Kinesis records from Lambda event."""
        service = KinesisService(client=kinesis_stream)

        # Create a sample Lambda event structure
        import base64

        coord = GPSCoordinate(
            truck_id="TRK-001",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            latitude=47.3769,
            longitude=8.5417,
            speed_kmh=45.5,
        )

        # Simulate Kinesis record in Lambda event
        records = [
            {
                "kinesis": {
                    "data": base64.b64encode(
                        coord.model_dump_json().encode("utf-8")
                    ).decode("utf-8"),
                    "sequenceNumber": "12345",
                },
                "eventID": "event-1",
            }
        ]

        parsed = service.parse_kinesis_records(records)

        assert len(parsed) == 1
        assert parsed[0].truck_id == "TRK-001"
        assert parsed[0].latitude == 47.3769

    def test_parse_invalid_record(self, kinesis_stream):
        """Test parsing invalid Kinesis record."""
        service = KinesisService(client=kinesis_stream)

        import base64

        # Invalid JSON data
        records = [
            {
                "kinesis": {
                    "data": base64.b64encode(b"invalid json").decode("utf-8"),
                    "sequenceNumber": "12345",
                },
            }
        ]

        parsed = service.parse_kinesis_records(records)

        # Should return empty list for invalid records
        assert len(parsed) == 0
