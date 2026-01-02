"""Notification handler - processes SNS events."""

import json
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.services.notification_service import NotificationService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handle SNS notification events.

    Processes notifications from various topics and can send emails,
    trigger webhooks, or perform other notification actions.
    """
    notification_service = NotificationService()

    records = event.get("Records", [])
    results = []

    for record in records:
        try:
            # Parse SNS message
            sns = record.get("Sns", {})
            topic_arn = sns.get("TopicArn", "")
            subject = sns.get("Subject", "")
            message = sns.get("Message", "")

            # Try to parse message as JSON
            try:
                message_data = json.loads(message)
            except json.JSONDecodeError:
                message_data = {"raw_message": message}

            logger.info(
                "Processing notification",
                topic_arn=topic_arn,
                subject=subject,
            )

            # Route based on topic or message content
            result = process_notification(
                notification_service,
                topic_arn,
                subject,
                message_data,
            )

            results.append({
                "topic": topic_arn.split(":")[-1] if topic_arn else "unknown",
                "status": "processed",
                "result": result,
            })

        except Exception as e:
            logger.exception("Failed to process notification")
            results.append({
                "topic": record.get("Sns", {}).get("TopicArn", "unknown"),
                "status": "failed",
                "error": str(e),
            })

    return {
        "statusCode": 200,
        "body": {
            "processed": len([r for r in results if r["status"] == "processed"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "results": results,
        },
    }


def process_notification(
    notification_service: NotificationService,
    topic_arn: str,
    subject: str,
    message_data: dict[str, Any],
) -> dict[str, Any]:
    """Process a single notification based on type."""
    topic_name = topic_arn.split(":")[-1] if topic_arn else ""

    # Determine notification type
    if "success" in topic_name.lower():
        return process_success_notification(notification_service, message_data)
    elif "failure" in topic_name.lower():
        return process_failure_notification(notification_service, message_data)
    elif "alert" in topic_name.lower():
        return process_alert_notification(notification_service, message_data)
    else:
        return process_generic_notification(notification_service, subject, message_data)


def process_success_notification(
    notification_service: NotificationService,
    message_data: dict[str, Any],
) -> dict[str, Any]:
    """Process success notification."""
    document_id = message_data.get("document_id", "unknown")

    logger.info(
        "Document processing succeeded",
        document_id=document_id,
    )

    # Could send email, trigger webhook, update dashboard, etc.
    # For now, just log and return

    return {
        "type": "success",
        "document_id": document_id,
        "action": "logged",
    }


def process_failure_notification(
    notification_service: NotificationService,
    message_data: dict[str, Any],
) -> dict[str, Any]:
    """Process failure notification."""
    document_id = message_data.get("document_id", "unknown")
    error = message_data.get("error", message_data.get("raw_message", "Unknown error"))

    logger.error(
        "Document processing failed",
        document_id=document_id,
        error=error,
    )

    # Could send alert email, trigger PagerDuty, etc.

    return {
        "type": "failure",
        "document_id": document_id,
        "error": error,
        "action": "logged",
    }


def process_alert_notification(
    notification_service: NotificationService,
    message_data: dict[str, Any],
) -> dict[str, Any]:
    """Process alert notification (model drift, errors, etc.)."""
    alert_type = message_data.get("alert_type", "Unknown")
    alert_message = message_data.get("message", "")
    details = message_data.get("details", {})

    logger.warning(
        "Alert received",
        alert_type=alert_type,
        message=alert_message,
    )

    # Could trigger escalation, send to ops channel, etc.

    return {
        "type": "alert",
        "alert_type": alert_type,
        "message": alert_message,
        "action": "logged",
    }


def process_generic_notification(
    notification_service: NotificationService,
    subject: str,
    message_data: dict[str, Any],
) -> dict[str, Any]:
    """Process generic notification."""
    logger.info(
        "Generic notification received",
        subject=subject,
    )

    return {
        "type": "generic",
        "subject": subject,
        "action": "logged",
    }
