"""Unit tests for data models."""

import json
from datetime import datetime

import pytest

from src.common.models import (
    AggregatedStats,
    AlertType,
    EngineStatus,
    Geofence,
    GeofenceAlert,
    GeofenceType,
    GPSCoordinate,
    TruckPosition,
)


class TestGPSCoordinate:
    """Tests for GPSCoordinate model."""

    def test_create_valid_coordinate(self):
        """Test creating a valid GPS coordinate."""
        coord = GPSCoordinate(
            truck_id="TRK-001",
            latitude=47.3769,
            longitude=8.5417,
            speed_kmh=45.5,
        )

        assert coord.truck_id == "TRK-001"
        assert coord.latitude == 47.3769
        assert coord.longitude == 8.5417
        assert coord.speed_kmh == 45.5
        assert coord.engine_status == EngineStatus.RUNNING

    def test_coordinate_with_all_fields(self):
        """Test coordinate with all fields specified."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        coord = GPSCoordinate(
            truck_id="TRK-002",
            timestamp=timestamp,
            latitude=46.9480,
            longitude=7.4474,
            speed_kmh=60,
            heading=90,
            altitude_m=500,
            accuracy_m=3,
            fuel_level_pct=80,
            engine_status=EngineStatus.IDLE,
        )

        assert coord.timestamp == timestamp
        assert coord.heading == 90
        assert coord.altitude_m == 500
        assert coord.fuel_level_pct == 80
        assert coord.engine_status == EngineStatus.IDLE

    def test_latitude_validation(self):
        """Test latitude bounds validation."""
        with pytest.raises(ValueError):
            GPSCoordinate(truck_id="TRK-001", latitude=91, longitude=0)

        with pytest.raises(ValueError):
            GPSCoordinate(truck_id="TRK-001", latitude=-91, longitude=0)

    def test_longitude_validation(self):
        """Test longitude bounds validation."""
        with pytest.raises(ValueError):
            GPSCoordinate(truck_id="TRK-001", latitude=0, longitude=181)

        with pytest.raises(ValueError):
            GPSCoordinate(truck_id="TRK-001", latitude=0, longitude=-181)

    def test_to_kinesis_record(self):
        """Test converting to Kinesis record format."""
        coord = GPSCoordinate(
            truck_id="TRK-001",
            latitude=47.3769,
            longitude=8.5417,
        )

        record = coord.to_kinesis_record()

        assert "Data" in record
        assert "PartitionKey" in record
        assert record["PartitionKey"] == "TRK-001"
        assert isinstance(record["Data"], bytes)

        # Verify data can be parsed back
        data = json.loads(record["Data"].decode("utf-8"))
        assert data["truck_id"] == "TRK-001"


class TestTruckPosition:
    """Tests for TruckPosition model."""

    def test_create_position(self):
        """Test creating a truck position."""
        pos = TruckPosition(
            truck_id="TRK-001",
            last_update=datetime.utcnow(),
            latitude=47.3769,
            longitude=8.5417,
        )

        assert pos.truck_id == "TRK-001"
        assert pos.speed_kmh == 0

    def test_to_dynamodb_item(self):
        """Test converting to DynamoDB item format."""
        pos = TruckPosition(
            truck_id="TRK-001",
            last_update=datetime(2024, 1, 15, 10, 30, 0),
            latitude=47.3769,
            longitude=8.5417,
            speed_kmh=45,
            ttl=1705312200,
        )

        item = pos.to_dynamodb_item()

        assert item["truck_id"]["S"] == "TRK-001"
        assert item["latitude"]["N"] == "47.3769"
        assert item["longitude"]["N"] == "8.5417"
        assert item["speed_kmh"]["N"] == "45"


class TestGeofence:
    """Tests for Geofence model."""

    def test_create_circle_geofence(self):
        """Test creating a circular geofence."""
        geofence = Geofence(
            geofence_id="GF-001",
            name="Main Warehouse",
            geofence_type=GeofenceType.CIRCLE,
            center_latitude=47.3769,
            center_longitude=8.5417,
            radius_meters=500,
            alert_on=AlertType.BOTH,
        )

        assert geofence.geofence_id == "GF-001"
        assert geofence.geofence_type == GeofenceType.CIRCLE
        assert geofence.radius_meters == 500

    def test_create_polygon_geofence(self):
        """Test creating a polygon geofence."""
        geofence = Geofence(
            geofence_id="GF-002",
            name="Delivery Zone",
            geofence_type=GeofenceType.POLYGON,
            center_latitude=47.0,
            center_longitude=8.0,
            polygon_coordinates=[
                (47.0, 8.0),
                (47.1, 8.0),
                (47.1, 8.1),
                (47.0, 8.1),
            ],
        )

        assert len(geofence.polygon_coordinates) == 4


class TestGeofenceAlert:
    """Tests for GeofenceAlert model."""

    def test_create_alert(self):
        """Test creating a geofence alert."""
        alert = GeofenceAlert(
            alert_id="ALT-001",
            truck_id="TRK-001",
            geofence_id="GF-001",
            geofence_name="Main Warehouse",
            alert_type="exit",
            timestamp=datetime.utcnow(),
            latitude=47.3769,
            longitude=8.5417,
        )

        assert alert.alert_type == "exit"

    def test_to_sns_message(self):
        """Test converting to SNS message."""
        alert = GeofenceAlert(
            alert_id="ALT-001",
            truck_id="TRK-001",
            geofence_id="GF-001",
            geofence_name="Main Warehouse",
            alert_type="enter",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            latitude=47.3769,
            longitude=8.5417,
        )

        message = alert.to_sns_message()
        data = json.loads(message)

        assert data["truck_id"] == "TRK-001"
        assert data["alert_type"] == "enter"


class TestAggregatedStats:
    """Tests for AggregatedStats model."""

    def test_create_stats(self):
        """Test creating aggregated statistics."""
        stats = AggregatedStats(
            truck_id="TRK-001",
            period_start=datetime(2024, 1, 15, 10, 0, 0),
            period_end=datetime(2024, 1, 15, 11, 0, 0),
            total_distance_km=42.5,
            average_speed_kmh=38.2,
            max_speed_kmh=85,
            idle_time_minutes=12,
            coordinates_count=720,
        )

        assert stats.total_distance_km == 42.5
        assert stats.coordinates_count == 720

    def test_to_parquet_record(self):
        """Test converting to Parquet-compatible dict."""
        stats = AggregatedStats(
            truck_id="TRK-001",
            period_start=datetime(2024, 1, 15, 10, 0, 0),
            period_end=datetime(2024, 1, 15, 11, 0, 0),
            total_distance_km=42.5,
            average_speed_kmh=38.2,
        )

        record = stats.to_parquet_record()

        assert record["truck_id"] == "TRK-001"
        assert record["total_distance_km"] == 42.5
