"""Custom exceptions for the GPS tracking system."""


class GPSTrackingError(Exception):
    """Base exception for GPS tracking errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class KinesisError(GPSTrackingError):
    """Exception for Kinesis-related errors."""

    pass


class GeofenceError(GPSTrackingError):
    """Exception for geofence-related errors."""

    pass


class ValidationError(GPSTrackingError):
    """Exception for data validation errors."""

    pass


class ConfigurationError(GPSTrackingError):
    """Exception for configuration errors."""

    pass
