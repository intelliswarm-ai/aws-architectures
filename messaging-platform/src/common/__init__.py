"""Common utilities and shared components."""

from .config import settings
from .exceptions import (
    SMSMarketingException,
    ConfigurationError,
    ValidationError,
    ProcessingError,
)

__all__ = [
    "settings",
    "SMSMarketingException",
    "ConfigurationError",
    "ValidationError",
    "ProcessingError",
]
