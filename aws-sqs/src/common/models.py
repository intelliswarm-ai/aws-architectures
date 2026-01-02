"""Data models for the banking platform."""

import re
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class TransactionType(str, Enum):
    """Types of banking transactions."""

    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    BALANCE_CHECK = "BALANCE_CHECK"


class TransactionStatus(str, Enum):
    """Transaction processing status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DUPLICATE = "DUPLICATE"


class Currency(str, Enum):
    """Supported currencies (ISO 4217)."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"
    JPY = "JPY"


ACCOUNT_PATTERN = re.compile(r"^\d{10,12}$")


class Transaction(BaseModel):
    """Banking transaction model."""

    transaction_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique transaction identifier",
    )
    transaction_type: TransactionType = Field(
        ...,
        description="Type of transaction",
    )
    source_account: str = Field(
        ...,
        min_length=10,
        max_length=12,
        description="Source account number",
    )
    target_account: str | None = Field(
        default=None,
        description="Target account number (for transfers/payments)",
    )
    amount: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Transaction amount",
    )
    currency: Currency = Field(
        default=Currency.USD,
        description="Transaction currency",
    )
    description: str | None = Field(
        default=None,
        max_length=256,
        description="Transaction description",
    )
    idempotency_key: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Unique key for idempotency",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Transaction timestamp",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    @field_validator("source_account", "target_account")
    @classmethod
    def validate_account_format(cls, v: str | None) -> str | None:
        """Validate account number format."""
        if v is None:
            return v
        if not ACCOUNT_PATTERN.match(v):
            raise ValueError("Account number must be 10-12 digits")
        return v

    @field_validator("target_account")
    @classmethod
    def validate_target_for_transfer(
        cls,
        v: str | None,
        info: Any,
    ) -> str | None:
        """Validate target account is provided for transfers."""
        values = info.data
        if values.get("transaction_type") in (
            TransactionType.TRANSFER,
            TransactionType.PAYMENT,
        ):
            if v is None:
                raise ValueError(
                    "Target account required for transfers and payments"
                )
        return v

    def to_sqs_message(self) -> dict[str, Any]:
        """Convert to SQS message format."""
        return {
            "MessageBody": self.model_dump_json(),
            "MessageAttributes": {
                "TransactionType": {
                    "DataType": "String",
                    "StringValue": self.transaction_type.value,
                },
                "Currency": {
                    "DataType": "String",
                    "StringValue": self.currency.value,
                },
            },
            "MessageDeduplicationId": self.idempotency_key,
            "MessageGroupId": self.source_account,
        }

    def to_dynamodb_item(self) -> dict[str, dict[str, str]]:
        """Convert to DynamoDB item format."""
        item = {
            "transaction_id": {"S": self.transaction_id},
            "transaction_type": {"S": self.transaction_type.value},
            "source_account": {"S": self.source_account},
            "amount": {"N": str(self.amount)},
            "currency": {"S": self.currency.value},
            "idempotency_key": {"S": self.idempotency_key},
            "timestamp": {"S": self.timestamp.isoformat()},
        }
        if self.target_account:
            item["target_account"] = {"S": self.target_account}
        if self.description:
            item["description"] = {"S": self.description}
        return item

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


class TransactionResult(BaseModel):
    """Result of transaction processing."""

    transaction_id: str = Field(..., description="Transaction ID")
    status: TransactionStatus = Field(..., description="Processing status")
    processed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Processing timestamp",
    )
    processor_id: str | None = Field(
        default=None,
        description="ID of processor that handled the transaction",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if failed",
    )
    error_code: str | None = Field(
        default=None,
        description="Error code if failed",
    )
    new_balance: Decimal | None = Field(
        default=None,
        description="Account balance after transaction",
    )

    def to_dynamodb_item(self) -> dict[str, dict[str, str]]:
        """Convert to DynamoDB item format."""
        item = {
            "transaction_id": {"S": self.transaction_id},
            "status": {"S": self.status.value},
            "processed_at": {"S": self.processed_at.isoformat()},
        }
        if self.processor_id:
            item["processor_id"] = {"S": self.processor_id}
        if self.error_message:
            item["error_message"] = {"S": self.error_message}
        if self.error_code:
            item["error_code"] = {"S": self.error_code}
        if self.new_balance is not None:
            item["new_balance"] = {"N": str(self.new_balance)}
        return item


class QueueMetrics(BaseModel):
    """SQS queue metrics for monitoring."""

    queue_url: str = Field(..., description="SQS queue URL")
    approximate_messages: int = Field(
        default=0,
        description="Approximate number of visible messages",
    )
    approximate_messages_not_visible: int = Field(
        default=0,
        description="Approximate number of in-flight messages",
    )
    approximate_messages_delayed: int = Field(
        default=0,
        description="Approximate number of delayed messages",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Metrics timestamp",
    )

    @property
    def total_messages(self) -> int:
        """Total messages in queue."""
        return (
            self.approximate_messages
            + self.approximate_messages_not_visible
            + self.approximate_messages_delayed
        )


class ScalingDecision(BaseModel):
    """Auto scaling decision based on queue metrics."""

    current_instances: int = Field(..., description="Current instance count")
    desired_instances: int = Field(..., description="Desired instance count")
    queue_depth: int = Field(..., description="Current queue depth")
    messages_per_instance: float = Field(
        ...,
        description="Messages per instance ratio",
    )
    action: str = Field(
        ...,
        description="Scaling action (scale_out, scale_in, no_change)",
    )
    reason: str = Field(..., description="Reason for scaling decision")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Decision timestamp",
    )
