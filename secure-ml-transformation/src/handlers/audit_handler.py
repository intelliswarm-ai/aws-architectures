"""Lambda handler for audit log management and queries."""

import json
from datetime import datetime, timedelta
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.config import get_settings
from src.common.models import AuditEventType, AuditLogEntry
from src.services.audit_service import AuditService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Handle audit log operations.

    Supports operations:
    - log_event: Log an audit event
    - query_logs: Query audit logs with filters
    - get_compliance_report: Generate compliance report
    - get_job_audit_trail: Get complete audit trail for a job

    Args:
        event: Lambda event payload
        context: Lambda context

    Returns:
        Operation response
    """
    audit_service = AuditService()

    operation = event.get("operation", "query_logs")
    logger.info("Processing audit operation", extra={"operation": operation})

    try:
        if operation == "log_event":
            return _log_event(event, audit_service)

        elif operation == "query_logs":
            return _query_logs(event, audit_service)

        elif operation == "get_compliance_report":
            return _get_compliance_report(event, audit_service)

        elif operation == "get_job_audit_trail":
            return _get_job_audit_trail(event, audit_service)

        elif operation == "get_pii_access_log":
            return _get_pii_access_log(event, audit_service)

        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Unknown operation: {operation}"}),
            }

    except Exception as e:
        logger.exception("Audit operation failed")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }


def _log_event(
    event: dict[str, Any],
    audit_service: AuditService,
) -> dict[str, Any]:
    """Log an audit event.

    Args:
        event: Event with audit data
        audit_service: Audit service instance

    Returns:
        Response with log result
    """
    audit_data = event.get("audit", {})

    audit_entry = AuditLogEntry(
        timestamp=datetime.fromisoformat(audit_data["timestamp"]) if audit_data.get("timestamp") else datetime.utcnow(),
        event_type=AuditEventType(audit_data.get("event_type", "JOB_START")),
        job_execution_id=audit_data.get("job_execution_id", "unknown"),
        job_name=audit_data.get("job_name"),
        user_identity=audit_data.get("user_identity"),
        source_ip=audit_data.get("source_ip"),
        resource_arn=audit_data.get("resource_arn"),
        action=audit_data.get("action"),
        details=audit_data.get("details", {}),
        status=audit_data.get("status", "SUCCESS"),
    )

    audit_service.log_event(audit_entry)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Audit event logged successfully",
                "event_type": audit_entry.event_type.value,
                "job_execution_id": audit_entry.job_execution_id,
            }
        ),
    }


def _query_logs(
    event: dict[str, Any],
    audit_service: AuditService,
) -> dict[str, Any]:
    """Query audit logs with filters.

    Args:
        event: Event with query parameters
        audit_service: Audit service instance

    Returns:
        Response with matching logs
    """
    # Extract query parameters
    start_time = event.get("start_time")
    end_time = event.get("end_time")
    event_types = event.get("event_types", [])
    job_execution_id = event.get("job_execution_id")
    limit = event.get("limit", 100)

    # Default to last 24 hours if no time range specified
    if not start_time:
        start_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    if not end_time:
        end_time = datetime.utcnow().isoformat()

    logs = audit_service.query_logs(
        start_time=datetime.fromisoformat(start_time),
        end_time=datetime.fromisoformat(end_time),
        event_types=[AuditEventType(et) for et in event_types] if event_types else None,
        job_execution_id=job_execution_id,
        limit=limit,
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "count": len(logs),
                "start_time": start_time,
                "end_time": end_time,
                "logs": [log.model_dump(mode="json") for log in logs],
            }
        ),
    }


def _get_compliance_report(
    event: dict[str, Any],
    audit_service: AuditService,
) -> dict[str, Any]:
    """Generate compliance report for a time period.

    Args:
        event: Event with report parameters
        audit_service: Audit service instance

    Returns:
        Response with compliance report
    """
    start_time = event.get("start_time")
    end_time = event.get("end_time")
    report_type = event.get("report_type", "summary")

    # Default to last 30 days
    if not start_time:
        start_time = (datetime.utcnow() - timedelta(days=30)).isoformat()
    if not end_time:
        end_time = datetime.utcnow().isoformat()

    report = audit_service.generate_compliance_report(
        start_time=datetime.fromisoformat(start_time),
        end_time=datetime.fromisoformat(end_time),
        report_type=report_type,
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "report_type": report_type,
                "period": {
                    "start": start_time,
                    "end": end_time,
                },
                "report": report,
            }
        ),
    }


def _get_job_audit_trail(
    event: dict[str, Any],
    audit_service: AuditService,
) -> dict[str, Any]:
    """Get complete audit trail for a job execution.

    Args:
        event: Event with job_execution_id
        audit_service: Audit service instance

    Returns:
        Response with job audit trail
    """
    job_execution_id = event.get("job_execution_id")

    if not job_execution_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "job_execution_id is required"}),
        }

    audit_trail = audit_service.get_job_audit_trail(job_execution_id)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "job_execution_id": job_execution_id,
                "event_count": len(audit_trail),
                "audit_trail": [entry.model_dump(mode="json") for entry in audit_trail],
            }
        ),
    }


def _get_pii_access_log(
    event: dict[str, Any],
    audit_service: AuditService,
) -> dict[str, Any]:
    """Get PII access log for compliance.

    Args:
        event: Event with query parameters
        audit_service: Audit service instance

    Returns:
        Response with PII access logs
    """
    start_time = event.get("start_time")
    end_time = event.get("end_time")
    column_name = event.get("column_name")

    # Default to last 7 days
    if not start_time:
        start_time = (datetime.utcnow() - timedelta(days=7)).isoformat()
    if not end_time:
        end_time = datetime.utcnow().isoformat()

    pii_logs = audit_service.get_pii_access_log(
        start_time=datetime.fromisoformat(start_time),
        end_time=datetime.fromisoformat(end_time),
        column_name=column_name,
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "period": {
                    "start": start_time,
                    "end": end_time,
                },
                "column_filter": column_name,
                "access_count": len(pii_logs),
                "pii_access_logs": pii_logs,
            }
        ),
    }
