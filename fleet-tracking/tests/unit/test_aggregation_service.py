"""Unit tests for aggregation service."""

from datetime import datetime

import pytest

from src.common.models import EngineStatus, GPSCoordinate
from src.services.aggregation_service import AggregationService


class TestAggregationService:
    """Tests for AggregationService."""

    @pytest.fixture
    def aggregation_service(self):
        """Create an aggregation service instance."""
        return AggregationService()

    def test_calculate_distance_same_point(self, aggregation_service):
        """Test distance calculation for same point."""
        distance = aggregation_service._calculate_distance(
            47.3769, 8.5417, 47.3769, 8.5417
        )
        assert distance == 0

    def test_calculate_distance_known_points(self, aggregation_service):
        """Test distance calculation for known points."""
        # Approximately 1km difference
        distance = aggregation_service._calculate_distance(
            47.3769, 8.5417,
            47.3859, 8.5417,  # ~1km north
        )
        assert 900 < distance < 1100  # ~1km with tolerance

    def test_aggregate_empty_list(self, aggregation_service):
        """Test aggregating empty coordinate list."""
        result = aggregation_service.aggregate_coordinates([])
        assert result == {}

    def test_aggregate_single_coordinate(self, aggregation_service):
        """Test aggregating single coordinate."""
        coord = GPSCoordinate(
            truck_id="TRK-001",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            latitude=47.3769,
            longitude=8.5417,
            speed_kmh=50,
        )

        result = aggregation_service.aggregate_coordinates([coord])

        assert "TRK-001" in result
        stats = result["TRK-001"]
        assert stats.coordinates_count == 1
        assert stats.total_distance_km == 0  # Only one point
        assert stats.average_speed_kmh == 50

    def test_aggregate_multiple_coordinates_single_truck(self, aggregation_service):
        """Test aggregating multiple coordinates for one truck."""
        coordinates = [
            GPSCoordinate(
                truck_id="TRK-001",
                timestamp=datetime(2024, 1, 15, 10, 0, i * 5),
                latitude=47.3769 + (i * 0.001),
                longitude=8.5417,
                speed_kmh=40 + i,
            )
            for i in range(5)
        ]

        result = aggregation_service.aggregate_coordinates(coordinates)

        assert "TRK-001" in result
        stats = result["TRK-001"]
        assert stats.coordinates_count == 5
        assert stats.total_distance_km > 0
        assert stats.average_speed_kmh == 42  # Average of 40,41,42,43,44
        assert stats.max_speed_kmh == 44

    def test_aggregate_multiple_trucks(self, aggregation_service):
        """Test aggregating coordinates for multiple trucks."""
        coordinates = [
            GPSCoordinate(
                truck_id="TRK-001",
                timestamp=datetime(2024, 1, 15, 10, 0, 0),
                latitude=47.3769,
                longitude=8.5417,
                speed_kmh=50,
            ),
            GPSCoordinate(
                truck_id="TRK-002",
                timestamp=datetime(2024, 1, 15, 10, 0, 0),
                latitude=46.9480,
                longitude=7.4474,
                speed_kmh=60,
            ),
            GPSCoordinate(
                truck_id="TRK-001",
                timestamp=datetime(2024, 1, 15, 10, 0, 5),
                latitude=47.3770,
                longitude=8.5418,
                speed_kmh=55,
            ),
        ]

        result = aggregation_service.aggregate_coordinates(coordinates)

        assert len(result) == 2
        assert "TRK-001" in result
        assert "TRK-002" in result
        assert result["TRK-001"].coordinates_count == 2
        assert result["TRK-002"].coordinates_count == 1

    def test_aggregate_idle_time(self, aggregation_service):
        """Test calculating idle time."""
        coordinates = [
            GPSCoordinate(
                truck_id="TRK-001",
                timestamp=datetime(2024, 1, 15, 10, 0, 0),
                latitude=47.3769,
                longitude=8.5417,
                speed_kmh=50,
                engine_status=EngineStatus.RUNNING,
            ),
            GPSCoordinate(
                truck_id="TRK-001",
                timestamp=datetime(2024, 1, 15, 10, 1, 0),  # 1 minute later
                latitude=47.3770,
                longitude=8.5418,
                speed_kmh=0,
                engine_status=EngineStatus.IDLE,
            ),
            GPSCoordinate(
                truck_id="TRK-001",
                timestamp=datetime(2024, 1, 15, 10, 2, 0),  # Another minute
                latitude=47.3770,
                longitude=8.5418,
                speed_kmh=0,
                engine_status=EngineStatus.IDLE,
            ),
        ]

        result = aggregation_service.aggregate_coordinates(coordinates)
        stats = result["TRK-001"]

        # Should have 2 minutes of idle time (from 2nd and 3rd coordinate)
        assert stats.idle_time_minutes == 2.0

    def test_calculate_stats_sorted_timestamps(self, aggregation_service):
        """Test that coordinates are sorted by timestamp."""
        # Provide coordinates out of order
        coordinates = [
            GPSCoordinate(
                truck_id="TRK-001",
                timestamp=datetime(2024, 1, 15, 10, 0, 10),  # Third
                latitude=47.3771,
                longitude=8.5419,
                speed_kmh=45,
            ),
            GPSCoordinate(
                truck_id="TRK-001",
                timestamp=datetime(2024, 1, 15, 10, 0, 0),  # First
                latitude=47.3769,
                longitude=8.5417,
                speed_kmh=50,
            ),
            GPSCoordinate(
                truck_id="TRK-001",
                timestamp=datetime(2024, 1, 15, 10, 0, 5),  # Second
                latitude=47.3770,
                longitude=8.5418,
                speed_kmh=55,
            ),
        ]

        result = aggregation_service.aggregate_coordinates(coordinates)
        stats = result["TRK-001"]

        # Period should be from first to last timestamp (when sorted)
        assert stats.period_start == datetime(2024, 1, 15, 10, 0, 0)
        assert stats.period_end == datetime(2024, 1, 15, 10, 0, 10)
