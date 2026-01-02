"""EventBridge Event Router Handler.

This handler processes EventBridge events, supporting cross-account event
patterns for enterprise event-driven architectures.
"""

from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.clients import get_aws_clients
from src.common.config import get_settings
from src.common.exceptions import NonRetryableError
from src.common.utils import generate_event_id, utc_now_iso

logger = Logger()
tracer = Tracer()
metrics = Metrics()

settings = get_settings()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """EventBridge event handler.

    Args:
        event: EventBridge event
        context: Lambda context

    Returns:
        Processing result
    """
    event_id = event.get("id", generate_event_id())
    detail_type = event.get("detail-type", "unknown")
    source = event.get("source", "unknown")
    account = event.get("account", "")
    region = event.get("region", "")

    logger.info(
        "Processing EventBridge event",
        extra={
            "event_id": event_id,
            "detail_type": detail_type,
            "source": source,
            "account": account,
            "region": region,
        },
    )

    try:
        detail = event.get("detail", {})

        # Check if this is a cross-account event
        is_cross_account = account != "" and account != get_current_account()

        if is_cross_account:
            logger.info(f"Processing cross-account event from {account}")
            metrics.add_metric(name="CrossAccountEvents", unit=MetricUnit.Count, value=1)

        # Route to appropriate handler based on source and detail-type
        result = route_event(source, detail_type, detail, event)

        metrics.add_metric(name="EventsProcessed", unit=MetricUnit.Count, value=1)
        metrics.add_dimension(name="Source", value=source)
        metrics.add_dimension(name="DetailType", value=detail_type)

        return {
            "status": "success",
            "event_id": event_id,
            "detail_type": detail_type,
            "result": result,
        }

    except NonRetryableError as e:
        logger.error(f"Non-retryable error: {e.message}")
        metrics.add_metric(name="EventsFailed", unit=MetricUnit.Count, value=1)
        return {
            "status": "failed",
            "event_id": event_id,
            "error": e.message,
        }

    except Exception as e:
        logger.exception(f"Unexpected error processing event: {e}")
        metrics.add_metric(name="EventsError", unit=MetricUnit.Count, value=1)
        raise


@tracer.capture_method
def get_current_account() -> str:
    """Get the current AWS account ID."""
    clients = get_aws_clients()
    identity = clients.sts.get_caller_identity()
    return identity["Account"]


@tracer.capture_method
def route_event(
    source: str,
    detail_type: str,
    detail: dict[str, Any],
    full_event: dict[str, Any],
) -> Any:
    """Route event to appropriate handler.

    Args:
        source: Event source
        detail_type: Event detail type
        detail: Event detail payload
        full_event: Complete event for context

    Returns:
        Handler result
    """
    # Define event handlers by source and detail-type
    handlers = {
        # Internal application events
        ("enterprise-api", "TenantCreated"): handle_tenant_created,
        ("enterprise-api", "TenantUpdated"): handle_tenant_updated,
        ("enterprise-api", "TenantDeleted"): handle_tenant_deleted,
        ("enterprise-api", "ResourceCreated"): handle_resource_event,
        ("enterprise-api", "ResourceUpdated"): handle_resource_event,
        ("enterprise-api", "ResourceDeleted"): handle_resource_event,
        # AWS service events
        ("aws.s3", "Object Created"): handle_s3_event,
        ("aws.dynamodb", "Stream Record"): handle_dynamodb_event,
        # Cross-account events
        ("partner-service", "DataAvailable"): handle_partner_event,
        ("partner-service", "SyncRequest"): handle_partner_sync,
    }

    handler_key = (source, detail_type)
    handler_func = handlers.get(handler_key)

    if handler_func:
        return handler_func(detail, full_event)

    # Check for wildcard handlers (handle all events from a source)
    wildcard_handlers = {
        "aws.cloudtrail": handle_cloudtrail_event,
        "aws.config": handle_config_event,
    }

    if source in wildcard_handlers:
        return wildcard_handlers[source](detail_type, detail, full_event)

    logger.warning(f"No handler for event: {source}/{detail_type}")
    return {"status": "ignored", "reason": "no_handler"}


def handle_tenant_created(detail: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Handle tenant creation events."""
    tenant_id = detail.get("tenant_id")
    logger.info(f"Processing tenant created event: {tenant_id}")

    # Publish to SQS for async processing
    publish_to_queue("tenant.created", {"tenant_id": tenant_id, **detail})

    return {"tenant_id": tenant_id, "action": "queued_for_processing"}


def handle_tenant_updated(detail: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Handle tenant update events."""
    tenant_id = detail.get("tenant_id")
    logger.info(f"Processing tenant updated event: {tenant_id}")

    publish_to_queue("tenant.updated", {"tenant_id": tenant_id, **detail})

    return {"tenant_id": tenant_id, "action": "queued_for_processing"}


def handle_tenant_deleted(detail: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Handle tenant deletion events."""
    tenant_id = detail.get("tenant_id")
    logger.info(f"Processing tenant deleted event: {tenant_id}")

    publish_to_queue("tenant.deleted", {"tenant_id": tenant_id, **detail})

    return {"tenant_id": tenant_id, "action": "queued_for_processing"}


def handle_resource_event(detail: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Handle resource lifecycle events."""
    resource_id = detail.get("resource_id")
    action = event.get("detail-type", "").replace("Resource", "").lower()

    logger.info(f"Processing resource {action} event: {resource_id}")

    return {"resource_id": resource_id, "action": action}


def handle_s3_event(detail: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Handle S3 events."""
    bucket = detail.get("bucket", {}).get("name")
    key = detail.get("object", {}).get("key")

    logger.info(f"Processing S3 event: s3://{bucket}/{key}")

    return {"bucket": bucket, "key": key, "action": "processed"}


def handle_dynamodb_event(detail: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Handle DynamoDB stream events."""
    table_name = detail.get("tableName")
    event_name = detail.get("eventName")

    logger.info(f"Processing DynamoDB event: {table_name} - {event_name}")

    return {"table": table_name, "event": event_name}


def handle_partner_event(detail: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Handle cross-account partner events."""
    partner_id = detail.get("partner_id")
    data_type = detail.get("data_type")

    logger.info(f"Processing partner event from {partner_id}: {data_type}")

    # Validate the event is from a trusted account
    source_account = event.get("account")
    # TODO: Validate against trusted account list

    return {"partner_id": partner_id, "data_type": data_type, "action": "received"}


def handle_partner_sync(detail: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Handle partner sync requests."""
    partner_id = detail.get("partner_id")
    sync_type = detail.get("sync_type")

    logger.info(f"Processing sync request from {partner_id}: {sync_type}")

    return {"partner_id": partner_id, "sync_type": sync_type, "action": "initiated"}


def handle_cloudtrail_event(
    detail_type: str,
    detail: dict[str, Any],
    event: dict[str, Any],
) -> dict[str, Any]:
    """Handle CloudTrail events for security monitoring."""
    event_name = detail.get("eventName")
    user_identity = detail.get("userIdentity", {})
    source_ip = detail.get("sourceIPAddress")

    logger.info(f"Processing CloudTrail event: {event_name}")

    # Check for security-relevant events
    security_events = [
        "ConsoleLogin",
        "CreateUser",
        "DeleteUser",
        "AttachUserPolicy",
        "CreateAccessKey",
        "PutBucketPolicy",
        "AuthorizeSecurityGroupIngress",
    ]

    if event_name in security_events:
        logger.warning(f"Security-relevant event detected: {event_name}")
        # TODO: Send alert via SNS

    return {"event_name": event_name, "source_ip": source_ip}


def handle_config_event(
    detail_type: str,
    detail: dict[str, Any],
    event: dict[str, Any],
) -> dict[str, Any]:
    """Handle AWS Config events for compliance monitoring."""
    config_rule_name = detail.get("configRuleName")
    compliance_type = detail.get("newEvaluationResult", {}).get("complianceType")

    logger.info(f"Processing Config event: {config_rule_name} - {compliance_type}")

    if compliance_type == "NON_COMPLIANT":
        logger.warning(f"Non-compliant resource detected by {config_rule_name}")
        # TODO: Send alert and/or trigger remediation

    return {"rule": config_rule_name, "compliance": compliance_type}


@tracer.capture_method
def publish_to_queue(message_type: str, payload: dict[str, Any]) -> None:
    """Publish message to SQS for async processing.

    Args:
        message_type: Type of message
        payload: Message payload
    """
    if not settings.processing_queue_url:
        logger.warning("No processing queue configured, skipping publish")
        return

    import json

    clients = get_aws_clients()
    clients.sqs.send_message(
        QueueUrl=settings.processing_queue_url,
        MessageBody=json.dumps({
            "type": message_type,
            "payload": payload,
            "timestamp": utc_now_iso(),
        }),
    )

    logger.info(f"Published {message_type} message to queue")
