"""Lambda handlers for the GPS tracking system."""

from .gps_producer import handler as gps_producer_handler
from .dashboard_consumer import handler as dashboard_consumer_handler
from .geofence_consumer import handler as geofence_consumer_handler
from .archive_consumer import handler as archive_consumer_handler

__all__ = [
    "gps_producer_handler",
    "dashboard_consumer_handler",
    "geofence_consumer_handler",
    "archive_consumer_handler",
]
