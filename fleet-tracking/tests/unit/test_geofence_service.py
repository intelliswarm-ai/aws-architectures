"""Unit tests for geofence service."""

from datetime import datetime

import pytest

from src.common.models import AlertType, Geofence, GeofenceType, GPSCoordinate
from src.services.geofence_service import GeofenceService


class TestGeofenceService:
    """Tests for GeofenceService."""

    @pytest.fixture
    def geofence_service(self):
        """Create a geofence service instance."""
        return GeofenceService()

    @pytest.fixture
    def circle_geofence(self):
        """Create a circular geofence for testing."""
        return Geofence(
            geofence_id="GF-001",
            name="Test Warehouse",
            geofence_type=GeofenceType.CIRCLE,
            center_latitude=47.3769,
            center_longitude=8.5417,
            radius_meters=500,
            alert_on=AlertType.BOTH,
        )

    def test_haversine_distance_same_point(self, geofence_service):
        """Test distance calculation for same point."""
        distance = geofence_service._haversine_distance(
            47.3769, 8.5417, 47.3769, 8.5417
        )
        assert distance == 0

    def test_haversine_distance_known_distance(self, geofence_service):
        """Test distance calculation for known coordinates."""
        # Zurich to Bern (approx 95 km)
        distance = geofence_service._haversine_distance(
            47.3769, 8.5417,  # Zurich
            46.9480, 7.4474,  # Bern
        )
        # Should be approximately 95km (95000m)
        assert 90000 < distance < 100000

    def test_is_inside_circle_inside(self, geofence_service, circle_geofence):
        """Test point inside circular geofence."""
        coord = GPSCoordinate(
            truck_id="TRK-001",
            latitude=47.3769,  # Same as center
            longitude=8.5417,
        )

        is_inside = geofence_service._is_inside_circle(coord, circle_geofence)
        assert is_inside is True

    def test_is_inside_circle_outside(self, geofence_service, circle_geofence):
        """Test point outside circular geofence."""
        coord = GPSCoordinate(
            truck_id="TRK-001",
            latitude=47.4,  # Far from center
            longitude=8.6,
        )

        is_inside = geofence_service._is_inside_circle(coord, circle_geofence)
        assert is_inside is False

    def test_is_inside_circle_on_boundary(self, geofence_service, circle_geofence):
        """Test point on geofence boundary."""
        # 500m is approximately 0.0045 degrees at this latitude
        coord = GPSCoordinate(
            truck_id="TRK-001",
            latitude=47.3769 + 0.0044,  # Just inside
            longitude=8.5417,
        )

        is_inside = geofence_service._is_inside_circle(coord, circle_geofence)
        assert is_inside is True

    def test_check_coordinate_enter_alert(self, geofence_service, circle_geofence):
        """Test generating enter alert."""
        # Add geofence to cache
        geofence_service._geofences_cache[circle_geofence.geofence_id] = circle_geofence

        # First, truck is outside
        outside_coord = GPSCoordinate(
            truck_id="TRK-001",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            latitude=47.4,
            longitude=8.6,
        )
        geofence_service.check_coordinate(outside_coord)

        # Then, truck moves inside
        inside_coord = GPSCoordinate(
            truck_id="TRK-001",
            timestamp=datetime(2024, 1, 15, 10, 0, 5),
            latitude=47.3769,
            longitude=8.5417,
        )
        alerts = geofence_service.check_coordinate(inside_coord)

        assert len(alerts) == 1
        assert alerts[0].alert_type == "enter"
        assert alerts[0].geofence_id == "GF-001"

    def test_check_coordinate_exit_alert(self, geofence_service, circle_geofence):
        """Test generating exit alert."""
        geofence_service._geofences_cache[circle_geofence.geofence_id] = circle_geofence

        # First, truck is inside
        inside_coord = GPSCoordinate(
            truck_id="TRK-002",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            latitude=47.3769,
            longitude=8.5417,
        )
        geofence_service.check_coordinate(inside_coord)

        # Then, truck moves outside
        outside_coord = GPSCoordinate(
            truck_id="TRK-002",
            timestamp=datetime(2024, 1, 15, 10, 0, 5),
            latitude=47.4,
            longitude=8.6,
        )
        alerts = geofence_service.check_coordinate(outside_coord)

        assert len(alerts) == 1
        assert alerts[0].alert_type == "exit"

    def test_check_coordinate_no_alert_when_staying(self, geofence_service, circle_geofence):
        """Test no alert when truck stays inside geofence."""
        geofence_service._geofences_cache[circle_geofence.geofence_id] = circle_geofence

        # Truck inside
        coord1 = GPSCoordinate(
            truck_id="TRK-003",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            latitude=47.3769,
            longitude=8.5417,
        )
        geofence_service.check_coordinate(coord1)

        # Truck still inside
        coord2 = GPSCoordinate(
            truck_id="TRK-003",
            timestamp=datetime(2024, 1, 15, 10, 0, 5),
            latitude=47.3770,  # Slightly moved but still inside
            longitude=8.5418,
        )
        alerts = geofence_service.check_coordinate(coord2)

        assert len(alerts) == 0

    def test_alert_on_exit_only(self, geofence_service):
        """Test geofence that only alerts on exit."""
        exit_only_geofence = Geofence(
            geofence_id="GF-002",
            name="Exit Only Zone",
            geofence_type=GeofenceType.CIRCLE,
            center_latitude=47.0,
            center_longitude=8.0,
            radius_meters=500,
            alert_on=AlertType.EXIT,
        )
        geofence_service._geofences_cache["GF-002"] = exit_only_geofence

        # Outside -> Inside (no alert expected)
        outside = GPSCoordinate(
            truck_id="TRK-004",
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            latitude=47.1,
            longitude=8.1,
        )
        geofence_service.check_coordinate(outside)

        inside = GPSCoordinate(
            truck_id="TRK-004",
            timestamp=datetime(2024, 1, 15, 10, 0, 5),
            latitude=47.0,
            longitude=8.0,
        )
        alerts = geofence_service.check_coordinate(inside)
        assert len(alerts) == 0  # No enter alert

        # Inside -> Outside (alert expected)
        outside_again = GPSCoordinate(
            truck_id="TRK-004",
            timestamp=datetime(2024, 1, 15, 10, 0, 10),
            latitude=47.1,
            longitude=8.1,
        )
        alerts = geofence_service.check_coordinate(outside_again)
        assert len(alerts) == 1
        assert alerts[0].alert_type == "exit"
