"""CloudTrail Audit Event Handler.

This handler processes CloudTrail events for security monitoring,
compliance alerting, and anomaly detection.
"""

from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.clients import get_aws_clients
from src.common.config import get_settings
from src.common.models import AuditEvent, AuditEventType
from src.common.utils import generate_event_id, json_dumps, json_loads

logger = Logger()
tracer = Tracer()
metrics = Metrics()

settings = get_settings()

# Security-critical events that require immediate alerting
CRITICAL_EVENTS = {
    "ConsoleLogin": "Authentication",
    "CreateUser": "IAM",
    "DeleteUser": "IAM",
    "CreateAccessKey": "IAM",
    "DeleteAccessKey": "IAM",
    "AttachUserPolicy": "IAM",
    "DetachUserPolicy": "IAM",
    "AttachRolePolicy": "IAM",
    "PutUserPolicy": "IAM",
    "PutRolePolicy": "IAM",
    "CreateRole": "IAM",
    "DeleteRole": "IAM",
    "UpdateAssumeRolePolicy": "IAM",
    "CreatePolicy": "IAM",
    "DeletePolicy": "IAM",
    "PutBucketPolicy": "S3",
    "DeleteBucketPolicy": "S3",
    "PutBucketAcl": "S3",
    "PutBucketPublicAccessBlock": "S3",
    "AuthorizeSecurityGroupIngress": "EC2",
    "AuthorizeSecurityGroupEgress": "EC2",
    "CreateSecurityGroup": "EC2",
    "DeleteSecurityGroup": "EC2",
    "ModifyDBInstance": "RDS",
    "DeleteDBInstance": "RDS",
    "CreateDBSnapshot": "RDS",
    "ModifyDBCluster": "RDS",
    "PutKeyPolicy": "KMS",
    "ScheduleKeyDeletion": "KMS",
    "DisableKey": "KMS",
    "StopLogging": "CloudTrail",
    "DeleteTrail": "CloudTrail",
    "UpdateTrail": "CloudTrail",
    "PutEventSelectors": "CloudTrail",
}

# Events that indicate potential security issues
SUSPICIOUS_PATTERNS = [
    "Failed",
    "Denied",
    "Unauthorized",
    "AccessDenied",
    "InvalidAccessKeyId",
    "SignatureDoesNotMatch",
]


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Process CloudTrail events from CloudWatch Logs.

    Args:
        event: CloudWatch Logs event with CloudTrail records
        context: Lambda context

    Returns:
        Processing result
    """
    # CloudWatch Logs delivers events in a compressed format
    import base64
    import gzip

    log_data = event.get("awslogs", {}).get("data", "")
    if not log_data:
        logger.warning("No log data in event")
        return {"status": "no_data"}

    # Decompress and parse
    compressed = base64.b64decode(log_data)
    uncompressed = gzip.decompress(compressed)
    log_events = json_loads(uncompressed)

    log_group = log_events.get("logGroup", "")
    log_stream = log_events.get("logStream", "")
    messages = log_events.get("logEvents", [])

    logger.info(
        f"Processing {len(messages)} CloudTrail events",
        extra={"log_group": log_group, "log_stream": log_stream},
    )

    processed = 0
    alerts = 0

    for log_event in messages:
        try:
            message = json_loads(log_event.get("message", "{}"))
            result = process_cloudtrail_event(message)

            if result.get("alert_sent"):
                alerts += 1
            processed += 1

        except Exception as e:
            logger.warning(f"Failed to process event: {e}")

    metrics.add_metric(name="AuditEventsProcessed", unit=MetricUnit.Count, value=processed)
    metrics.add_metric(name="SecurityAlertsSent", unit=MetricUnit.Count, value=alerts)

    return {
        "status": "success",
        "processed": processed,
        "alerts": alerts,
    }


@tracer.capture_method
def process_cloudtrail_event(event: dict[str, Any]) -> dict[str, Any]:
    """Process a single CloudTrail event.

    Args:
        event: CloudTrail event record

    Returns:
        Processing result
    """
    event_name = event.get("eventName", "")
    event_source = event.get("eventSource", "")
    event_time = event.get("eventTime", "")
    aws_region = event.get("awsRegion", "")

    user_identity = event.get("userIdentity", {})
    source_ip = event.get("sourceIPAddress", "")
    user_agent = event.get("userAgent", "")
    error_code = event.get("errorCode")
    error_message = event.get("errorMessage")

    # Extract user information
    principal_id = user_identity.get("principalId", "")
    user_type = user_identity.get("type", "")
    arn = user_identity.get("arn", "")
    account_id = user_identity.get("accountId", "")

    result: dict[str, Any] = {
        "event_name": event_name,
        "processed": True,
        "alert_sent": False,
    }

    # Check for critical security events
    if event_name in CRITICAL_EVENTS:
        category = CRITICAL_EVENTS[event_name]
        logger.warning(
            f"Critical security event: {event_name}",
            extra={
                "category": category,
                "user": arn,
                "source_ip": source_ip,
                "region": aws_region,
            },
        )

        # Create audit event
        audit_event = AuditEvent(
            event_id=generate_event_id(),
            event_type=AuditEventType.CONFIG_CHANGE,
            tenant_id=account_id,
            user_id=principal_id,
            source_ip=source_ip,
            user_agent=user_agent,
            resource=event_source,
            action=event_name,
            result="success" if not error_code else "failure",
            details={
                "category": category,
                "arn": arn,
                "region": aws_region,
                "error_code": error_code,
                "error_message": error_message,
            },
        )

        # Store audit event
        store_audit_event(audit_event)

        # Send alert for critical events
        if settings.alert_topic_arn:
            send_security_alert(event, category)
            result["alert_sent"] = True

        metrics.add_metric(name="CriticalSecurityEvents", unit=MetricUnit.Count, value=1)
        metrics.add_dimension(name="Category", value=category)

    # Check for failed/denied events (potential attacks)
    if error_code and any(pattern in str(error_code) for pattern in SUSPICIOUS_PATTERNS):
        logger.warning(
            f"Suspicious event: {event_name} - {error_code}",
            extra={
                "error_message": error_message,
                "user": arn,
                "source_ip": source_ip,
            },
        )

        audit_event = AuditEvent(
            event_id=generate_event_id(),
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            tenant_id=account_id,
            user_id=principal_id,
            source_ip=source_ip,
            user_agent=user_agent,
            resource=event_source,
            action=event_name,
            result="denied",
            details={
                "error_code": error_code,
                "error_message": error_message,
                "arn": arn,
            },
        )

        store_audit_event(audit_event)

        metrics.add_metric(name="SuspiciousEvents", unit=MetricUnit.Count, value=1)

    # Check for console logins
    if event_name == "ConsoleLogin":
        login_result = event.get("responseElements", {}).get("ConsoleLogin", "")
        mfa_used = event.get("additionalEventData", {}).get("MFAUsed", "No")

        event_type = (
            AuditEventType.LOGIN_SUCCESS if login_result == "Success" else AuditEventType.LOGIN_FAILURE
        )

        audit_event = AuditEvent(
            event_id=generate_event_id(),
            event_type=event_type,
            tenant_id=account_id,
            user_id=principal_id,
            source_ip=source_ip,
            user_agent=user_agent,
            action="ConsoleLogin",
            result=login_result.lower(),
            details={
                "mfa_used": mfa_used,
                "user_type": user_type,
            },
        )

        store_audit_event(audit_event)

        if login_result != "Success":
            logger.warning(f"Failed console login from {source_ip}")
            metrics.add_metric(name="FailedLogins", unit=MetricUnit.Count, value=1)

    return result


@tracer.capture_method
def store_audit_event(event: AuditEvent) -> None:
    """Store audit event in DynamoDB.

    Args:
        event: Audit event to store
    """
    if not settings.audit_table:
        logger.debug("No audit table configured, skipping storage")
        return

    try:
        clients = get_aws_clients()
        table = clients.dynamodb_resource.Table(settings.audit_table)

        item = {
            "PK": f"EVENT#{event.event_id}",
            "SK": event.timestamp.isoformat(),
            "event_type": event.event_type.value,
            "tenant_id": event.tenant_id,
            "user_id": event.user_id,
            "source_ip": event.source_ip,
            "user_agent": event.user_agent,
            "resource": event.resource,
            "action": event.action,
            "result": event.result,
            "details": event.details,
            "ttl": int(datetime.utcnow().timestamp()) + (90 * 24 * 60 * 60),  # 90 days
        }

        # Remove None values
        item = {k: v for k, v in item.items() if v is not None}

        table.put_item(Item=item)
        logger.debug(f"Stored audit event: {event.event_id}")

    except Exception as e:
        logger.error(f"Failed to store audit event: {e}")


@tracer.capture_method
def send_security_alert(event: dict[str, Any], category: str) -> None:
    """Send security alert via SNS.

    Args:
        event: CloudTrail event that triggered the alert
        category: Security category
    """
    if not settings.alert_topic_arn:
        return

    try:
        clients = get_aws_clients()

        event_name = event.get("eventName", "Unknown")
        user_identity = event.get("userIdentity", {})
        source_ip = event.get("sourceIPAddress", "Unknown")
        region = event.get("awsRegion", "Unknown")

        subject = f"Security Alert: {category} - {event_name}"
        message = {
            "alert_type": "security",
            "category": category,
            "event_name": event_name,
            "user": user_identity.get("arn", "Unknown"),
            "source_ip": source_ip,
            "region": region,
            "timestamp": event.get("eventTime"),
            "details": event,
        }

        clients.sns.publish(
            TopicArn=settings.alert_topic_arn,
            Subject=subject[:100],  # SNS subject limit
            Message=json_dumps(message),
            MessageAttributes={
                "category": {"DataType": "String", "StringValue": category},
                "severity": {"DataType": "String", "StringValue": "high"},
            },
        )

        logger.info(f"Security alert sent: {subject}")

    except Exception as e:
        logger.error(f"Failed to send security alert: {e}")
