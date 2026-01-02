"""Unit tests for data models."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.common.models import (
    Currency,
    QueueMetrics,
    ScalingDecision,
    Transaction,
    TransactionResult,
    TransactionStatus,
    TransactionType,
)


class TestTransaction:
    """Tests for Transaction model."""

    def test_valid_transfer_transaction(self, sample_transaction_data):
        """Test creating a valid transfer transaction."""
        transaction = Transaction(**sample_transaction_data)

        assert transaction.transaction_type == TransactionType.TRANSFER
        assert transaction.source_account == "1234567890"
        assert transaction.target_account == "0987654321"
        assert transaction.amount == Decimal("100.00")
        assert transaction.currency == Currency.USD
        assert transaction.idempotency_key == "test-key-123"

    def test_auto_generated_transaction_id(self, sample_transaction_data):
        """Test that transaction_id is auto-generated."""
        transaction = Transaction(**sample_transaction_data)

        assert transaction.transaction_id is not None
        assert len(transaction.transaction_id) == 36  # UUID format

    def test_invalid_account_number_short(self):
        """Test that short account numbers are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Transaction(
                transaction_type=TransactionType.DEPOSIT,
                source_account="123",  # Too short
                amount=Decimal("100.00"),
                idempotency_key="test-key",
            )

        assert "source_account" in str(exc_info.value)

    def test_invalid_account_number_non_numeric(self):
        """Test that non-numeric account numbers are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Transaction(
                transaction_type=TransactionType.DEPOSIT,
                source_account="12345abcde",  # Contains letters
                amount=Decimal("100.00"),
                idempotency_key="test-key",
            )

        assert "Account number must be 10-12 digits" in str(exc_info.value)

    def test_negative_amount_rejected(self):
        """Test that negative amounts are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Transaction(
                transaction_type=TransactionType.DEPOSIT,
                source_account="1234567890",
                amount=Decimal("-100.00"),
                idempotency_key="test-key",
            )

        assert "amount" in str(exc_info.value)

    def test_transfer_requires_target_account(self):
        """Test that transfers require a target account."""
        with pytest.raises(ValidationError) as exc_info:
            Transaction(
                transaction_type=TransactionType.TRANSFER,
                source_account="1234567890",
                target_account=None,  # Missing
                amount=Decimal("100.00"),
                idempotency_key="test-key",
            )

        assert "Target account required" in str(exc_info.value)

    def test_deposit_does_not_require_target_account(self):
        """Test that deposits don't require a target account."""
        transaction = Transaction(
            transaction_type=TransactionType.DEPOSIT,
            source_account="1234567890",
            target_account=None,
            amount=Decimal("100.00"),
            idempotency_key="test-key",
        )

        assert transaction.target_account is None

    def test_to_sqs_message(self, sample_transaction_data):
        """Test conversion to SQS message format."""
        transaction = Transaction(**sample_transaction_data)
        message = transaction.to_sqs_message()

        assert "MessageBody" in message
        assert "MessageAttributes" in message
        assert message["MessageAttributes"]["TransactionType"]["StringValue"] == "TRANSFER"
        assert message["MessageAttributes"]["Currency"]["StringValue"] == "USD"

    def test_to_dynamodb_item(self, sample_transaction_data):
        """Test conversion to DynamoDB item format."""
        transaction = Transaction(**sample_transaction_data)
        item = transaction.to_dynamodb_item()

        assert item["transaction_id"]["S"] == transaction.transaction_id
        assert item["source_account"]["S"] == "1234567890"
        assert item["target_account"]["S"] == "0987654321"
        assert item["amount"]["N"] == "100.00"


class TestTransactionResult:
    """Tests for TransactionResult model."""

    def test_completed_result(self):
        """Test creating a completed result."""
        result = TransactionResult(
            transaction_id="test-txn-id",
            status=TransactionStatus.COMPLETED,
            processor_id="processor-1",
            new_balance=Decimal("500.00"),
        )

        assert result.status == TransactionStatus.COMPLETED
        assert result.new_balance == Decimal("500.00")
        assert result.error_message is None

    def test_failed_result(self):
        """Test creating a failed result."""
        result = TransactionResult(
            transaction_id="test-txn-id",
            status=TransactionStatus.FAILED,
            processor_id="processor-1",
            error_message="Insufficient funds",
            error_code="INSUFFICIENT_FUNDS",
        )

        assert result.status == TransactionStatus.FAILED
        assert result.error_message == "Insufficient funds"
        assert result.error_code == "INSUFFICIENT_FUNDS"

    def test_to_dynamodb_item(self):
        """Test conversion to DynamoDB item format."""
        result = TransactionResult(
            transaction_id="test-txn-id",
            status=TransactionStatus.COMPLETED,
            processor_id="processor-1",
        )
        item = result.to_dynamodb_item()

        assert item["transaction_id"]["S"] == "test-txn-id"
        assert item["status"]["S"] == "COMPLETED"
        assert item["processor_id"]["S"] == "processor-1"


class TestQueueMetrics:
    """Tests for QueueMetrics model."""

    def test_total_messages(self):
        """Test total messages calculation."""
        metrics = QueueMetrics(
            queue_url="https://sqs.test.com/queue",
            approximate_messages=100,
            approximate_messages_not_visible=25,
            approximate_messages_delayed=10,
        )

        assert metrics.total_messages == 135


class TestScalingDecision:
    """Tests for ScalingDecision model."""

    def test_scale_out_decision(self):
        """Test scale-out decision."""
        decision = ScalingDecision(
            current_instances=2,
            desired_instances=5,
            queue_depth=500,
            messages_per_instance=250.0,
            action="scale_out",
            reason="Queue depth exceeds target",
        )

        assert decision.action == "scale_out"
        assert decision.desired_instances > decision.current_instances

    def test_scale_in_decision(self):
        """Test scale-in decision."""
        decision = ScalingDecision(
            current_instances=5,
            desired_instances=2,
            queue_depth=50,
            messages_per_instance=10.0,
            action="scale_in",
            reason="Queue depth below target",
        )

        assert decision.action == "scale_in"
        assert decision.desired_instances < decision.current_instances
