"""Custom exceptions for the SMS Marketing System."""


class SMSMarketingException(Exception):
    """Base exception for SMS Marketing System."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(SMSMarketingException):
    """Raised when there's a configuration error."""

    pass


class ValidationError(SMSMarketingException):
    """Raised when validation fails."""

    pass


class ProcessingError(SMSMarketingException):
    """Raised when event processing fails."""

    pass


class KinesisError(SMSMarketingException):
    """Raised when Kinesis operations fail."""

    pass


class DynamoDBError(SMSMarketingException):
    """Raised when DynamoDB operations fail."""

    pass


class S3Error(SMSMarketingException):
    """Raised when S3 operations fail."""

    pass


class PinpointError(SMSMarketingException):
    """Raised when Pinpoint operations fail."""

    pass
