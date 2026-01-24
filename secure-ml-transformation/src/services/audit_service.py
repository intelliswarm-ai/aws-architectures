"""Service for audit logging and compliance tracking."""

import json
from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger

from src.common.clients import get_cloudwatch_logs_client
from src.common.config import get_settings
from src.common.models import AuditEventType, AuditLogEntry

logger = Logger()


class AuditService:
    """Service for audit logging and compliance."""

    def __init__(self) -> None:
        """Initialize audit service."""
        self._settings = get_settings()
        self._logs_client = get_cloudwatch_logs_client()
        self._log_group_name = f"/aws/glue/{self._settings.resource_prefix}/audit"

    def log_event(self, entry: AuditLogEntry) -> bool:
        """Log an audit event to CloudWatch.

        Args:
            entry: Audit log entry

        Returns:
            True if successful
        """
        try:
            # Ensure log group exists
            self._ensure_log_group()

            # Create log stream if needed (daily streams)
            log_stream = entry.timestamp.strftime("%Y/%m/%d")
            self._ensure_log_stream(log_stream)

            # Put log event
            self._logs_client.put_log_events(
                logGroupName=self._log_group_name,
                logStreamName=log_stream,
                logEvents=[
                    {
                        "timestamp": int(entry.timestamp.timestamp() * 1000),
                        "message": entry.to_cloudwatch_log(),
                    }
                ],
            )

            logger.debug(
                "Audit event logged",
                extra={
                    "event_type": entry.event_type.value,
                    "job_execution_id": entry.job_execution_id,
                },
            )

            return True

        except Exception as e:
            logger.exception("Failed to log audit event")
            return False

    def query_logs(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: list[AuditEventType] | None = None,
        job_execution_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Query audit logs with filters.

        Args:
            start_time: Start of query range
            end_time: End of query range
            event_types: Filter by event types
            job_execution_id: Filter by job execution ID
            limit: Maximum results

        Returns:
            List of matching audit entries
        """
        try:
            # Build filter pattern
            filter_patterns = []
            if event_types:
                type_patterns = [f'$.event_type = "{et.value}"' for et in event_types]
                filter_patterns.append(f"({' || '.join(type_patterns)})")
            if job_execution_id:
                filter_patterns.append(f'$.job_execution_id = "{job_execution_id}"')

            filter_pattern = " && ".join(filter_patterns) if filter_patterns else ""

            response = self._logs_client.filter_log_events(
                logGroupName=self._log_group_name,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                filterPattern=filter_pattern if filter_pattern else None,
                limit=limit,
            )

            entries = []
            for event in response.get("events", []):
                try:
                    data = json.loads(event["message"])
                    entry = AuditLogEntry(
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        event_type=AuditEventType(data["event_type"]),
                        job_execution_id=data["job_execution_id"],
                        job_name=data.get("job_name"),
                        user_identity=data.get("user_identity"),
                        resource_arn=data.get("resource_arn"),
                        action=data.get("action"),
                        details=data.get("details", {}),
                        status=data.get("status", "SUCCESS"),
                    )
                    entries.append(entry)
                except Exception as e:
                    logger.warning(f"Failed to parse audit entry: {e}")
                    continue

            return entries

        except Exception as e:
            logger.exception("Failed to query audit logs")
            return []

    def get_job_audit_trail(
        self,
        job_execution_id: str,
    ) -> list[AuditLogEntry]:
        """Get complete audit trail for a job.

        Args:
            job_execution_id: Job execution ID

        Returns:
            List of audit entries for the job
        """
        # Query last 30 days for this job
        end_time = datetime.utcnow()
        start_time = datetime(end_time.year, end_time.month - 1 if end_time.month > 1 else 12, end_time.day)

        return self.query_logs(
            start_time=start_time,
            end_time=end_time,
            job_execution_id=job_execution_id,
            limit=1000,
        )

    def generate_compliance_report(
        self,
        start_time: datetime,
        end_time: datetime,
        report_type: str = "summary",
    ) -> dict[str, Any]:
        """Generate compliance report for a period.

        Args:
            start_time: Report start time
            end_time: Report end time
            report_type: Type of report (summary, detailed)

        Returns:
            Compliance report data
        """
        # Get all logs for period
        logs = self.query_logs(
            start_time=start_time,
            end_time=end_time,
            limit=10000,
        )

        # Aggregate statistics
        event_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {"SUCCESS": 0, "FAILURE": 0, "IN_PROGRESS": 0}
        job_counts: dict[str, int] = {}
        pii_operations: list[dict[str, Any]] = []

        for entry in logs:
            # Count by event type
            event_type = entry.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

            # Count by status
            status_counts[entry.status] = status_counts.get(entry.status, 0) + 1

            # Count by job
            if entry.job_name:
                job_counts[entry.job_name] = job_counts.get(entry.job_name, 0) + 1

            # Track PII operations
            if entry.event_type in [AuditEventType.PII_DETECTION, AuditEventType.PII_TOKENIZATION]:
                pii_operations.append(
                    {
                        "timestamp": entry.timestamp.isoformat(),
                        "event_type": entry.event_type.value,
                        "job_execution_id": entry.job_execution_id,
                        "details": entry.details,
                    }
                )

        report = {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "total_events": len(logs),
            "event_counts": event_counts,
            "status_counts": status_counts,
            "job_counts": job_counts,
            "pii_operations_count": len(pii_operations),
            "success_rate": (
                status_counts["SUCCESS"] / len(logs) * 100 if logs else 0
            ),
        }

        if report_type == "detailed":
            report["pii_operations"] = pii_operations

        return report

    def get_pii_access_log(
        self,
        start_time: datetime,
        end_time: datetime,
        column_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get PII access log for compliance.

        Args:
            start_time: Start of query range
            end_time: End of query range
            column_name: Optional column name filter

        Returns:
            List of PII access records
        """
        logs = self.query_logs(
            start_time=start_time,
            end_time=end_time,
            event_types=[AuditEventType.PII_DETECTION, AuditEventType.PII_TOKENIZATION],
            limit=10000,
        )

        access_records = []
        for entry in logs:
            record = {
                "timestamp": entry.timestamp.isoformat(),
                "event_type": entry.event_type.value,
                "job_execution_id": entry.job_execution_id,
                "job_name": entry.job_name,
                "user_identity": entry.user_identity,
                "columns_accessed": entry.details.get("columns", []),
                "records_processed": entry.details.get("records_processed", 0),
            }

            # Apply column filter
            if column_name:
                if column_name not in record["columns_accessed"]:
                    continue

            access_records.append(record)

        return access_records

    def _ensure_log_group(self) -> None:
        """Ensure the audit log group exists."""
        try:
            self._logs_client.create_log_group(
                logGroupName=self._log_group_name,
                tags={
                    "Project": self._settings.project_name,
                    "Environment": self._settings.environment,
                },
            )

            # Set retention policy
            self._logs_client.put_retention_policy(
                logGroupName=self._log_group_name,
                retentionInDays=self._settings.log_retention_days,
            )

        except self._logs_client.exceptions.ResourceAlreadyExistsException:
            pass

    def _ensure_log_stream(self, stream_name: str) -> None:
        """Ensure a log stream exists."""
        try:
            self._logs_client.create_log_stream(
                logGroupName=self._log_group_name,
                logStreamName=stream_name,
            )
        except self._logs_client.exceptions.ResourceAlreadyExistsException:
            pass
