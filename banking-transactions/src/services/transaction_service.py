"""Transaction processing service."""

import random
import time
from datetime import datetime
from decimal import Decimal
from typing import Any

from aws_lambda_powertools import Logger

from ..common.clients import get_dynamodb_client
from ..common.config import settings
from ..common.exceptions import (
    DuplicateTransactionError,
    InsufficientFundsError,
    InvalidAccountError,
    ProcessingError,
)
from ..common.models import (
    Transaction,
    TransactionResult,
    TransactionStatus,
    TransactionType,
)
from .idempotency_service import IdempotencyService

logger = Logger(service=settings.service_name)


class TransactionService:
    """Service for processing banking transactions."""

    def __init__(
        self,
        table_name: str | None = None,
        processor_id: str | None = None,
    ) -> None:
        """Initialize transaction service."""
        self.table_name = table_name or settings.transactions_table_name
        self.processor_id = processor_id or f"processor-{random.randint(1000, 9999)}"
        self.client = get_dynamodb_client()
        self.idempotency_service = IdempotencyService()

    def process_transaction(self, transaction: Transaction) -> TransactionResult:
        """Process a banking transaction.

        Args:
            transaction: Transaction to process.

        Returns:
            TransactionResult with processing outcome.
        """
        start_time = time.time()
        logger.info(
            "Processing transaction",
            extra={
                "transaction_id": transaction.transaction_id,
                "type": transaction.transaction_type.value,
                "amount": str(transaction.amount),
            },
        )

        try:
            # Check idempotency
            self.idempotency_service.check_and_set(
                transaction.idempotency_key,
                transaction.transaction_id,
            )
        except DuplicateTransactionError:
            return TransactionResult(
                transaction_id=transaction.transaction_id,
                status=TransactionStatus.DUPLICATE,
                processor_id=self.processor_id,
                error_message="Duplicate transaction",
                error_code="DUPLICATE_TRANSACTION",
            )

        try:
            # Validate accounts (simulated)
            self._validate_account(transaction.source_account)
            if transaction.target_account:
                self._validate_account(transaction.target_account)

            # Check funds (simulated)
            if transaction.transaction_type in (
                TransactionType.TRANSFER,
                TransactionType.WITHDRAWAL,
                TransactionType.PAYMENT,
            ):
                self._check_funds(transaction.source_account, transaction.amount)

            # Execute transaction (simulated)
            new_balance = self._execute_transaction(transaction)

            # Store result
            result = TransactionResult(
                transaction_id=transaction.transaction_id,
                status=TransactionStatus.COMPLETED,
                processor_id=self.processor_id,
                new_balance=new_balance,
            )
            self._store_result(transaction, result)

            processing_time = time.time() - start_time
            logger.info(
                "Transaction completed",
                extra={
                    "transaction_id": transaction.transaction_id,
                    "processing_time_ms": int(processing_time * 1000),
                    "new_balance": str(new_balance),
                },
            )
            return result

        except (InvalidAccountError, InsufficientFundsError) as e:
            # Remove idempotency record to allow retry with corrected data
            self.idempotency_service.remove(transaction.idempotency_key)

            result = TransactionResult(
                transaction_id=transaction.transaction_id,
                status=TransactionStatus.FAILED,
                processor_id=self.processor_id,
                error_message=str(e),
                error_code=e.error_code,
            )
            self._store_result(transaction, result)
            return result

        except Exception as e:
            logger.error(
                "Transaction processing failed",
                extra={
                    "transaction_id": transaction.transaction_id,
                    "error": str(e),
                },
            )
            # Remove idempotency record to allow retry
            self.idempotency_service.remove(transaction.idempotency_key)

            result = TransactionResult(
                transaction_id=transaction.transaction_id,
                status=TransactionStatus.FAILED,
                processor_id=self.processor_id,
                error_message=str(e),
                error_code="PROCESSING_ERROR",
            )
            self._store_result(transaction, result)
            return result

    def _validate_account(self, account_number: str) -> None:
        """Validate an account exists (simulated).

        In a real system, this would query an account database.
        """
        # Simulate account validation
        # Accounts starting with '0' are considered invalid for demo
        if account_number.startswith("0000"):
            raise InvalidAccountError(account_number)

    def _check_funds(self, account_number: str, amount: Decimal) -> None:
        """Check if account has sufficient funds (simulated).

        In a real system, this would check actual account balance.
        """
        # Simulate balance check
        # For demo, generate a random balance
        simulated_balance = Decimal(random.uniform(100, 10000)).quantize(
            Decimal("0.01")
        )

        # Small chance of insufficient funds for testing
        if random.random() < 0.05:  # 5% chance
            raise InsufficientFundsError(
                account_number,
                float(amount),
                float(simulated_balance),
            )

    def _execute_transaction(self, transaction: Transaction) -> Decimal:
        """Execute the transaction (simulated).

        In a real system, this would update account balances atomically.
        """
        # Simulate processing time (10-50ms)
        time.sleep(random.uniform(0.01, 0.05))

        # Return simulated new balance
        base_balance = Decimal(random.uniform(1000, 50000))

        if transaction.transaction_type in (
            TransactionType.DEPOSIT,
        ):
            return (base_balance + transaction.amount).quantize(Decimal("0.01"))
        elif transaction.transaction_type in (
            TransactionType.WITHDRAWAL,
            TransactionType.TRANSFER,
            TransactionType.PAYMENT,
        ):
            return (base_balance - transaction.amount).quantize(Decimal("0.01"))
        else:
            # Balance check
            return base_balance.quantize(Decimal("0.01"))

    def _store_result(
        self,
        transaction: Transaction,
        result: TransactionResult,
    ) -> None:
        """Store transaction and result in DynamoDB."""
        try:
            # Merge transaction and result items
            item = transaction.to_dynamodb_item()
            result_item = result.to_dynamodb_item()
            item.update(result_item)

            # Add TTL for automatic cleanup (90 days)
            ttl = int(time.time()) + (90 * 24 * 60 * 60)
            item["ttl"] = {"N": str(ttl)}

            self.client.put_item(
                TableName=self.table_name,
                Item=item,
            )
        except Exception as e:
            logger.error(
                "Failed to store transaction result",
                extra={
                    "transaction_id": transaction.transaction_id,
                    "error": str(e),
                },
            )
            raise ProcessingError(
                f"Failed to store result: {e}",
                transaction.transaction_id,
            ) from e

    def get_transaction(self, transaction_id: str) -> dict[str, Any] | None:
        """Get a transaction by ID.

        Args:
            transaction_id: Transaction ID to look up.

        Returns:
            Transaction data if found, None otherwise.
        """
        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={"transaction_id": {"S": transaction_id}},
            )
            return response.get("Item")
        except Exception as e:
            logger.error(
                "Failed to get transaction",
                extra={
                    "transaction_id": transaction_id,
                    "error": str(e),
                },
            )
            raise
