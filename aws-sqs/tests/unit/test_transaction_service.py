"""Unit tests for TransactionService."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.common.exceptions import (
    DuplicateTransactionError,
    InsufficientFundsError,
    InvalidAccountError,
)
from src.common.models import Transaction, TransactionStatus, TransactionType
from src.services.transaction_service import TransactionService


class TestTransactionService:
    """Tests for TransactionService."""

    @pytest.fixture
    def mock_dynamodb_client(self):
        """Create a mock DynamoDB client."""
        return MagicMock()

    @pytest.fixture
    def mock_idempotency_service(self):
        """Create a mock IdempotencyService."""
        mock = MagicMock()
        mock.check_and_set.return_value = True
        return mock

    @pytest.fixture
    def transaction_service(self, mock_dynamodb_client, mock_idempotency_service):
        """Create a TransactionService with mocked dependencies."""
        with patch("src.services.transaction_service.get_dynamodb_client", return_value=mock_dynamodb_client):
            with patch("src.services.transaction_service.IdempotencyService", return_value=mock_idempotency_service):
                service = TransactionService(
                    table_name="test-transactions",
                    processor_id="test-processor",
                )
                service.client = mock_dynamodb_client
                service.idempotency_service = mock_idempotency_service
                return service

    def test_process_deposit_transaction(self, transaction_service, sample_transaction_data):
        """Test processing a deposit transaction."""
        sample_transaction_data["transaction_type"] = "DEPOSIT"
        sample_transaction_data["target_account"] = None
        transaction = Transaction(**sample_transaction_data)

        result = transaction_service.process_transaction(transaction)

        assert result.status == TransactionStatus.COMPLETED
        assert result.processor_id == "test-processor"
        assert result.new_balance is not None

    def test_process_transfer_transaction(self, transaction_service, sample_transaction_data):
        """Test processing a transfer transaction."""
        transaction = Transaction(**sample_transaction_data)

        result = transaction_service.process_transaction(transaction)

        assert result.status == TransactionStatus.COMPLETED
        assert result.new_balance is not None

    def test_duplicate_transaction_detected(self, transaction_service, sample_transaction_data):
        """Test that duplicate transactions are detected."""
        transaction_service.idempotency_service.check_and_set.side_effect = (
            DuplicateTransactionError("test-key-123")
        )

        transaction = Transaction(**sample_transaction_data)
        result = transaction_service.process_transaction(transaction)

        assert result.status == TransactionStatus.DUPLICATE
        assert result.error_code == "DUPLICATE_TRANSACTION"

    def test_invalid_account_handling(self, transaction_service, sample_transaction_data):
        """Test handling of invalid account numbers."""
        sample_transaction_data["source_account"] = "0000567890"  # Invalid
        transaction = Transaction(**sample_transaction_data)

        result = transaction_service.process_transaction(transaction)

        assert result.status == TransactionStatus.FAILED
        assert result.error_code == "INVALID_ACCOUNT"
        # Verify idempotency record is removed on failure
        transaction_service.idempotency_service.remove.assert_called()

    def test_stores_result_in_dynamodb(self, transaction_service, sample_transaction_data):
        """Test that results are stored in DynamoDB."""
        transaction = Transaction(**sample_transaction_data)

        result = transaction_service.process_transaction(transaction)

        transaction_service.client.put_item.assert_called()
        call_args = transaction_service.client.put_item.call_args
        assert call_args.kwargs["TableName"] == "test-transactions"

    def test_get_transaction(self, transaction_service):
        """Test getting a transaction by ID."""
        transaction_service.client.get_item.return_value = {
            "Item": {
                "transaction_id": {"S": "test-txn-id"},
                "status": {"S": "COMPLETED"},
            }
        }

        result = transaction_service.get_transaction("test-txn-id")

        assert result["transaction_id"]["S"] == "test-txn-id"
        assert result["status"]["S"] == "COMPLETED"

    def test_get_transaction_not_found(self, transaction_service):
        """Test getting a non-existent transaction."""
        transaction_service.client.get_item.return_value = {}

        result = transaction_service.get_transaction("non-existent")

        assert result is None
