"""Notification service for SNS and SES."""

import json
from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.models import Document, ProcessingResult

logger = Logger()


class NotificationService:
    """Service for sending notifications via SNS and SES."""

    def __init__(self):
        self.settings = get_settings()
        self.clients = get_clients()

    def notify_success(
        self,
        document: Document,
        result: ProcessingResult | None = None,
    ) -> str:
        """Send success notification."""
        message = self._build_success_message(document, result)

        return self._publish_to_sns(
            topic_arn=self.settings.success_topic_arn,
            subject=f"Document Processed: {document.document_id}",
            message=message,
        )

    def notify_failure(
        self,
        document: Document,
        error: str,
        error_type: str = "ProcessingError",
    ) -> str:
        """Send failure notification."""
        message = self._build_failure_message(document, error, error_type)

        return self._publish_to_sns(
            topic_arn=self.settings.failure_topic_arn,
            subject=f"Document Processing Failed: {document.document_id}",
            message=message,
        )

    def notify_alert(
        self,
        alert_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> str:
        """Send alert notification (e.g., model drift, errors)."""
        alert_message = {
            "alert_type": alert_type,
            "message": message,
            "details": details or {},
        }

        return self._publish_to_sns(
            topic_arn=self.settings.alert_topic_arn,
            subject=f"ML Platform Alert: {alert_type}",
            message=json.dumps(alert_message, indent=2),
        )

    def notify_training_complete(
        self,
        job_name: str,
        model_artifacts_uri: str,
        metrics: dict[str, Any] | None = None,
    ) -> str:
        """Send training completion notification."""
        message = {
            "event": "TrainingComplete",
            "job_name": job_name,
            "model_artifacts": model_artifacts_uri,
            "metrics": metrics or {},
        }

        return self._publish_to_sns(
            topic_arn=self.settings.success_topic_arn,
            subject=f"Training Complete: {job_name}",
            message=json.dumps(message, indent=2),
        )

    def _publish_to_sns(
        self,
        topic_arn: str,
        subject: str,
        message: str,
    ) -> str:
        """Publish message to SNS topic."""
        if not topic_arn:
            logger.warning("No topic ARN configured, skipping notification")
            return ""

        try:
            response = self.clients.sns.publish(
                TopicArn=topic_arn,
                Subject=subject[:100],  # SNS subject limit
                Message=message,
                MessageAttributes={
                    "source": {
                        "DataType": "String",
                        "StringValue": "ml-platform",
                    }
                },
            )

            message_id = response.get("MessageId", "")
            logger.info(
                "Published notification",
                topic_arn=topic_arn,
                message_id=message_id,
            )
            return message_id

        except ClientError as e:
            logger.error(f"Failed to publish notification: {e}")
            raise

    def send_email(
        self,
        to_addresses: list[str],
        subject: str,
        body_text: str,
        body_html: str | None = None,
        from_address: str | None = None,
    ) -> str:
        """Send email via SES."""
        try:
            source = from_address or f"noreply@{self.settings.aws_region}.amazonaws.com"

            message: dict[str, Any] = {
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body_text}},
            }

            if body_html:
                message["Body"]["Html"] = {"Data": body_html}

            response = self.clients.ses.send_email(
                Source=source,
                Destination={"ToAddresses": to_addresses},
                Message=message,
            )

            message_id = response.get("MessageId", "")
            logger.info(
                "Sent email",
                message_id=message_id,
                recipients=to_addresses,
            )
            return message_id

        except ClientError as e:
            logger.error(f"Failed to send email: {e}")
            raise

    def _build_success_message(
        self,
        document: Document,
        result: ProcessingResult | None,
    ) -> str:
        """Build success notification message."""
        message_parts = [
            "Document processing completed successfully.",
            "",
            f"Document ID: {document.document_id}",
            f"Source: s3://{document.bucket}/{document.key}",
            f"Type: {document.document_type}",
            f"Status: {document.status}",
        ]

        if result:
            message_parts.extend([
                "",
                "Processing Results:",
            ])

            if result.extraction:
                message_parts.append(
                    f"  - Extracted {result.extraction.words} words "
                    f"({result.extraction.confidence:.1%} confidence)"
                )

            if result.analysis:
                message_parts.append(
                    f"  - Found {len(result.analysis.entities)} entities, "
                    f"{len(result.analysis.key_phrases)} key phrases"
                )
                if result.analysis.sentiment:
                    message_parts.append(
                        f"  - Sentiment: {result.analysis.sentiment.sentiment}"
                    )

            if result.inference:
                message_parts.append(
                    f"  - Classification: {result.inference.predicted_class} "
                    f"({result.inference.confidence:.1%} confidence)"
                )

            if result.generation:
                if result.generation.summary:
                    message_parts.append("  - Summary generated")
                if result.generation.questions:
                    message_parts.append(
                        f"  - Generated {len(result.generation.questions)} Q&A pairs"
                    )

            message_parts.append(
                f"\nProcessing time: {result.processing_time_ms:.0f}ms"
            )

        return "\n".join(message_parts)

    def _build_failure_message(
        self,
        document: Document,
        error: str,
        error_type: str,
    ) -> str:
        """Build failure notification message."""
        return "\n".join([
            "Document processing failed.",
            "",
            f"Document ID: {document.document_id}",
            f"Source: s3://{document.bucket}/{document.key}",
            f"Type: {document.document_type}",
            f"Retry Count: {document.retry_count}",
            "",
            f"Error Type: {error_type}",
            f"Error: {error}",
        ])
