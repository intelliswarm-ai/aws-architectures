"""Transaction processing worker for EC2 instances."""

import os
import signal
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from aws_lambda_powertools import Logger

from ..common.config import settings
from ..common.models import Transaction
from ..services.queue_service import QueueService
from ..services.transaction_service import TransactionService

logger = Logger(service=settings.service_name)


class TransactionWorker:
    """Worker that continuously processes transactions from SQS."""

    def __init__(
        self,
        queue_url: str | None = None,
        num_threads: int | None = None,
    ) -> None:
        """Initialize the transaction worker.

        Args:
            queue_url: SQS queue URL to poll.
            num_threads: Number of worker threads.
        """
        self.queue_service = QueueService(queue_url)
        self.transaction_service = TransactionService(
            processor_id=self._get_processor_id()
        )
        self.num_threads = num_threads or settings.worker_threads
        self.running = False
        self._shutdown_event = threading.Event()
        self._stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "duplicates": 0,
        }
        self._stats_lock = threading.Lock()

    def _get_processor_id(self) -> str:
        """Generate a unique processor ID."""
        hostname = socket.gethostname()
        instance_id = os.environ.get("EC2_INSTANCE_ID", "local")
        return f"{hostname}-{instance_id}"

    def _process_message(self, message: dict[str, Any]) -> None:
        """Process a single SQS message.

        Args:
            message: SQS message to process.
        """
        receipt_handle = message.get("ReceiptHandle")
        message_id = message.get("MessageId")

        try:
            # Parse transaction
            transaction = self.queue_service.parse_transaction(message)

            logger.info(
                "Processing message",
                extra={
                    "message_id": message_id,
                    "transaction_id": transaction.transaction_id,
                },
            )

            # Process transaction
            result = self.transaction_service.process_transaction(transaction)

            # Update stats
            with self._stats_lock:
                self._stats["processed"] += 1
                if result.status.value == "COMPLETED":
                    self._stats["succeeded"] += 1
                elif result.status.value == "DUPLICATE":
                    self._stats["duplicates"] += 1
                else:
                    self._stats["failed"] += 1

            # Delete message on success or duplicate
            if result.status.value in ("COMPLETED", "DUPLICATE"):
                self.queue_service.delete_message(receipt_handle)
                logger.info(
                    "Message processed successfully",
                    extra={
                        "message_id": message_id,
                        "status": result.status.value,
                    },
                )
            else:
                # Leave message for retry (will become visible after timeout)
                logger.warning(
                    "Transaction failed, leaving for retry",
                    extra={
                        "message_id": message_id,
                        "error": result.error_message,
                    },
                )

        except Exception as e:
            logger.error(
                "Error processing message",
                extra={
                    "message_id": message_id,
                    "error": str(e),
                },
            )
            with self._stats_lock:
                self._stats["failed"] += 1
            # Message will become visible again after visibility timeout

    def _poll_loop(self, thread_id: int) -> None:
        """Main polling loop for a worker thread.

        Args:
            thread_id: Identifier for this thread.
        """
        logger.info(f"Worker thread {thread_id} started")

        while not self._shutdown_event.is_set():
            try:
                # Long poll for messages
                messages = self.queue_service.receive_messages(
                    max_messages=settings.batch_size,
                    wait_time=settings.wait_time_seconds,
                )

                if not messages:
                    continue

                logger.debug(
                    f"Thread {thread_id} received {len(messages)} messages"
                )

                # Process each message
                for message in messages:
                    if self._shutdown_event.is_set():
                        break
                    self._process_message(message)

            except Exception as e:
                logger.error(
                    f"Thread {thread_id} error",
                    extra={"error": str(e)},
                )
                # Brief pause before retrying
                time.sleep(1)

        logger.info(f"Worker thread {thread_id} stopped")

    def start(self) -> None:
        """Start the worker threads."""
        if self.running:
            logger.warning("Worker already running")
            return

        self.running = True
        self._shutdown_event.clear()

        logger.info(
            "Starting transaction worker",
            extra={
                "num_threads": self.num_threads,
                "processor_id": self.transaction_service.processor_id,
            },
        )

        # Start worker threads
        self._executor = ThreadPoolExecutor(
            max_workers=self.num_threads,
            thread_name_prefix="txn-worker",
        )

        for i in range(self.num_threads):
            self._executor.submit(self._poll_loop, i)

        logger.info("Transaction worker started")

    def stop(self, timeout: float = 30) -> None:
        """Stop the worker gracefully.

        Args:
            timeout: Maximum time to wait for threads to finish.
        """
        if not self.running:
            return

        logger.info("Stopping transaction worker")
        self._shutdown_event.set()
        self.running = False

        # Wait for threads to finish
        self._executor.shutdown(wait=True, cancel_futures=False)

        logger.info(
            "Transaction worker stopped",
            extra={"stats": self._stats},
        )

    def get_stats(self) -> dict[str, int]:
        """Get processing statistics.

        Returns:
            Dictionary with processing stats.
        """
        with self._stats_lock:
            return dict(self._stats)


# Global worker instance
_worker: TransactionWorker | None = None


def get_worker() -> TransactionWorker:
    """Get or create the global worker instance."""
    global _worker
    if _worker is None:
        _worker = TransactionWorker()
    return _worker


def signal_handler(signum: int, frame: Any) -> None:
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down")
    if _worker:
        _worker.stop()


def main() -> None:
    """Main entry point for the worker application."""
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Start worker
    worker = get_worker()
    worker.start()

    # Keep main thread alive
    try:
        while worker.running:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        worker.stop()


if __name__ == "__main__":
    main()
