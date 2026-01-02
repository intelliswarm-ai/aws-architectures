"""Custom exceptions for the banking platform."""


class BankingError(Exception):
    """Base exception for banking errors."""

    def __init__(self, message: str, error_code: str = "BANKING_ERROR") -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(BankingError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None) -> None:
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class InvalidAccountError(BankingError):
    """Raised when an account number is invalid or not found."""

    def __init__(self, account_number: str) -> None:
        self.account_number = account_number
        super().__init__(
            f"Invalid or non-existent account: {account_number}",
            "INVALID_ACCOUNT",
        )


class InsufficientFundsError(BankingError):
    """Raised when an account has insufficient funds."""

    def __init__(
        self,
        account_number: str,
        requested_amount: float,
        available_balance: float,
    ) -> None:
        self.account_number = account_number
        self.requested_amount = requested_amount
        self.available_balance = available_balance
        super().__init__(
            f"Insufficient funds in account {account_number}: "
            f"requested {requested_amount}, available {available_balance}",
            "INSUFFICIENT_FUNDS",
        )


class DuplicateTransactionError(BankingError):
    """Raised when a duplicate transaction is detected."""

    def __init__(self, idempotency_key: str) -> None:
        self.idempotency_key = idempotency_key
        super().__init__(
            f"Duplicate transaction detected: {idempotency_key}",
            "DUPLICATE_TRANSACTION",
        )


class ProcessingError(BankingError):
    """Raised when transaction processing fails."""

    def __init__(self, message: str, transaction_id: str | None = None) -> None:
        self.transaction_id = transaction_id
        super().__init__(message, "PROCESSING_ERROR")


class QueueError(BankingError):
    """Raised when SQS operations fail."""

    def __init__(self, message: str, queue_url: str | None = None) -> None:
        self.queue_url = queue_url
        super().__init__(message, "QUEUE_ERROR")
