"""Lambda handlers for ML Canary Deployment system."""

from src.handlers.api_handler import handler as api_handler
from src.handlers.deployment_handler import handler as deployment_handler
from src.handlers.monitoring_handler import handler as monitoring_handler
from src.handlers.rollback_handler import handler as rollback_handler
from src.handlers.traffic_shift_handler import handler as traffic_shift_handler

__all__ = [
    "api_handler",
    "deployment_handler",
    "monitoring_handler",
    "traffic_shift_handler",
    "rollback_handler",
]
