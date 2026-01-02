"""Common utilities and shared components for GPS tracking system."""

from .config import Settings, get_settings
from .models import (
    GPSCoordinate,
    TruckPosition,
    Geofence,
    GeofenceAlert,
    AggregatedStats,
)
from .exceptions import (
    GPSTrackingError,
    KinesisError,
    GeofenceError,
    ValidationError,
)

__all__ = [
    "Settings",
    "get_settings",
    "GPSCoordinate",
    "TruckPosition",
    "Geofence",
    "GeofenceAlert",
    "AggregatedStats",
    "GPSTrackingError",
    "KinesisError",
    "GeofenceError",
    "ValidationError",
]
