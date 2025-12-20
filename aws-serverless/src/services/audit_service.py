"""Audit Service for logging and querying audit events.

Provides centralized audit logging for compliance and security monitoring.
"""

from datetime import datetime, timedelta
from typing import Any

from aws_lambda_powertools import Logger, Tracer

from src.common.clients import get_aws_clients, get_dynamodb_table
from src.common.config import get_settings
from src.common.models import AuditEvent, AuditEventType
from src.common.utils import generate_event_id, json_dumps, utc_now

logger = Logger()
tracer = Tracer()

settings = get_settings()


class AuditService:
    """Service for managing audit logs."""

    # Default retention period in days
    DEFAULT_RETENTION_DAYS = 90

    def __init__(self) -> None:
        self._clients = get_aws_clients()
        self._table_name = settings.audit_table

    @property
    def _table(self) -> Any:
        """Get DynamoDB table resource."""
        return get_dynamodb_table(self._table_name)

    @tracer.capture_method
    def log_event(
        self,
        event_type: AuditEventType,
        tenant_id: str | None = None,
        user_id: str | None = None,
        source_ip: str | None = None,
        user_agent: str | None = None,
        resource: str | None = None,
        action: str | None = None,
        result: str | None = None,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> AuditEvent:
        """Log an audit event.

        Args:
            event_type: Type of audit event
            tenant_id: Tenant ID (if applicable)
            user_id: User ID (if applicable)
            source_ip: Source IP address
            user_agent: User agent string
            resource: Resource being accessed
            action: Action being performed
            result: Result of the action
            details: Additional event details
            request_id: Request ID for correlation

        Returns:
            Created audit event
        """
        event = AuditEvent(
            event_id=generate_event_id(),
            event_type=event_type,
            timestamp=utc_now(),
            tenant_id=tenant_id,
            user_id=user_id,
            source_ip=source_ip,
            user_agent=user_agent,
            resource=resource,
            action=action,
            result=result,
            details=details or {},
            request_id=request_id,
        )

        # Store in DynamoDB
        self._store_event(event)

        # Log for CloudWatch
        logger.info(
            f"Audit event: {event_type.value}",
            extra={
                "event_id": event.event_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "result": result,
            },
        )

        # For critical events, also send alert
        if self._is_critical_event(event_type):
            self._send_alert(event)

        return event

    @tracer.capture_method
    def log_api_access(
        self,
        tenant_id: str,
        user_id: str,
        method: str,
        path: str,
        status_code: int,
        source_ip: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
        duration_ms: int | None = None,
    ) -> AuditEvent:
        """Log an API access event.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            method: HTTP method
            path: Request path
            status_code: Response status code
            source_ip: Source IP address
            user_agent: User agent string
            request_id: Request ID
            duration_ms: Request duration in milliseconds

        Returns:
            Created audit event
        """
        event_type = AuditEventType.DATA_READ if method == "GET" else AuditEventType.DATA_UPDATE

        result = "success" if 200 <= status_code < 400 else "failure"
        if status_code == 403:
            event_type = AuditEventType.ACCESS_DENIED
        elif status_code == 401:
            event_type = AuditEventType.LOGIN_FAILURE

        return self.log_event(
            event_type=event_type,
            tenant_id=tenant_id,
            user_id=user_id,
            source_ip=source_ip,
            user_agent=user_agent,
            resource=path,
            action=method,
            result=result,
            details={
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
            request_id=request_id,
        )

    @tracer.capture_method
    def log_login(
        self,
        user_id: str,
        tenant_id: str | None,
        success: bool,
        source_ip: str | None = None,
        user_agent: str | None = None,
        mfa_used: bool = False,
        failure_reason: str | None = None,
    ) -> AuditEvent:
        """Log a login event.

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            success: Whether login succeeded
            source_ip: Source IP address
            user_agent: User agent string
            mfa_used: Whether MFA was used
            failure_reason: Reason for failure (if applicable)

        Returns:
            Created audit event
        """
        event_type = AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE

        return self.log_event(
            event_type=event_type,
            tenant_id=tenant_id,
            user_id=user_id,
            source_ip=source_ip,
            user_agent=user_agent,
            action="login",
            result="success" if success else "failure",
            details={
                "mfa_used": mfa_used,
                "failure_reason": failure_reason,
            },
        )

    @tracer.capture_method
    def log_data_access(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool = True,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log a data access event.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            resource_type: Type of resource accessed
            resource_id: ID of resource accessed
            action: Action performed (create, read, update, delete)
            success: Whether action succeeded
            details: Additional details

        Returns:
            Created audit event
        """
        action_map = {
            "create": AuditEventType.DATA_CREATE,
            "read": AuditEventType.DATA_READ,
            "update": AuditEventType.DATA_UPDATE,
            "delete": AuditEventType.DATA_DELETE,
        }

        event_type = action_map.get(action.lower(), AuditEventType.DATA_READ)

        return self.log_event(
            event_type=event_type,
            tenant_id=tenant_id,
            user_id=user_id,
            resource=f"{resource_type}/{resource_id}",
            action=action,
            result="success" if success else "failure",
            details=details,
        )

    @tracer.capture_method
    def query_events(
        self,
        tenant_id: str | None = None,
        user_id: str | None = None,
        event_type: AuditEventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        last_key: str | None = None,
    ) -> tuple[list[AuditEvent], str | None]:
        """Query audit events with filters.

        Args:
            tenant_id: Filter by tenant ID
            user_id: Filter by user ID
            event_type: Filter by event type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
            last_key: Pagination token

        Returns:
            Tuple of (events list, next page token)
        """
        # Build query parameters based on available indexes
        if tenant_id:
            params = self._build_tenant_query(tenant_id, start_time, end_time, limit)
        elif user_id:
            params = self._build_user_query(user_id, start_time, end_time, limit)
        else:
            params = self._build_scan_query(start_time, end_time, limit)

        if event_type:
            params["FilterExpression"] = "event_type = :event_type"
            params["ExpressionAttributeValues"][":event_type"] = event_type.value

        if last_key:
            import json
            params["ExclusiveStartKey"] = json.loads(last_key)

        if "KeyConditionExpression" in params:
            response = self._table.query(**params)
        else:
            response = self._table.scan(**params)

        events = [self._item_to_event(item) for item in response.get("Items", [])]

        next_key = None
        if "LastEvaluatedKey" in response:
            import json
            next_key = json.dumps(response["LastEvaluatedKey"])

        return events, next_key

    @tracer.capture_method
    def get_event(self, event_id: str) -> AuditEvent | None:
        """Get a specific audit event.

        Args:
            event_id: Event ID

        Returns:
            Audit event or None if not found
        """
        response = self._table.get_item(
            Key={"PK": f"EVENT#{event_id}"}
        )

        item = response.get("Item")
        if not item:
            return None

        return self._item_to_event(item)

    @tracer.capture_method
    def get_user_activity(
        self,
        user_id: str,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get user activity summary.

        Args:
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Activity summary
        """
        end_time = utc_now()
        start_time = end_time - timedelta(days=days)

        events, _ = self.query_events(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000,
        )

        # Aggregate by event type
        by_type: dict[str, int] = {}
        by_day: dict[str, int] = {}
        by_resource: dict[str, int] = {}

        for event in events:
            # By type
            type_key = event.event_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # By day
            day_key = event.timestamp.strftime("%Y-%m-%d")
            by_day[day_key] = by_day.get(day_key, 0) + 1

            # By resource
            if event.resource:
                resource_key = event.resource.split("/")[0]
                by_resource[resource_key] = by_resource.get(resource_key, 0) + 1

        return {
            "user_id": user_id,
            "period_days": days,
            "total_events": len(events),
            "by_type": by_type,
            "by_day": by_day,
            "by_resource": by_resource,
        }

    def _store_event(self, event: AuditEvent) -> None:
        """Store audit event in DynamoDB.

        Args:
            event: Audit event to store
        """
        if not self._table_name:
            logger.debug("No audit table configured")
            return

        ttl = int((event.timestamp + timedelta(days=self.DEFAULT_RETENTION_DAYS)).timestamp())

        item = {
            "PK": f"EVENT#{event.event_id}",
            "SK": event.timestamp.isoformat(),
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "tenant_id": event.tenant_id,
            "user_id": event.user_id,
            "source_ip": event.source_ip,
            "user_agent": event.user_agent,
            "resource": event.resource,
            "action": event.action,
            "result": event.result,
            "details": event.details,
            "request_id": event.request_id,
            "ttl": ttl,
        }

        # Add GSI keys for querying
        if event.tenant_id:
            item["GSI1PK"] = f"TENANT#{event.tenant_id}"
            item["GSI1SK"] = event.timestamp.isoformat()

        if event.user_id:
            item["GSI2PK"] = f"USER#{event.user_id}"
            item["GSI2SK"] = event.timestamp.isoformat()

        # Remove None values
        item = {k: v for k, v in item.items() if v is not None}

        self._table.put_item(Item=item)

    def _build_tenant_query(
        self,
        tenant_id: str,
        start_time: datetime | None,
        end_time: datetime | None,
        limit: int,
    ) -> dict[str, Any]:
        """Build query for tenant-based filtering."""
        params: dict[str, Any] = {
            "IndexName": "GSI1",
            "KeyConditionExpression": "GSI1PK = :pk",
            "ExpressionAttributeValues": {":pk": f"TENANT#{tenant_id}"},
            "Limit": limit,
            "ScanIndexForward": False,
        }

        if start_time and end_time:
            params["KeyConditionExpression"] += " AND GSI1SK BETWEEN :start AND :end"
            params["ExpressionAttributeValues"][":start"] = start_time.isoformat()
            params["ExpressionAttributeValues"][":end"] = end_time.isoformat()

        return params

    def _build_user_query(
        self,
        user_id: str,
        start_time: datetime | None,
        end_time: datetime | None,
        limit: int,
    ) -> dict[str, Any]:
        """Build query for user-based filtering."""
        params: dict[str, Any] = {
            "IndexName": "GSI2",
            "KeyConditionExpression": "GSI2PK = :pk",
            "ExpressionAttributeValues": {":pk": f"USER#{user_id}"},
            "Limit": limit,
            "ScanIndexForward": False,
        }

        if start_time and end_time:
            params["KeyConditionExpression"] += " AND GSI2SK BETWEEN :start AND :end"
            params["ExpressionAttributeValues"][":start"] = start_time.isoformat()
            params["ExpressionAttributeValues"][":end"] = end_time.isoformat()

        return params

    def _build_scan_query(
        self,
        start_time: datetime | None,
        end_time: datetime | None,
        limit: int,
    ) -> dict[str, Any]:
        """Build scan query (fallback when no index available)."""
        params: dict[str, Any] = {
            "Limit": limit,
            "ExpressionAttributeValues": {},
        }

        if start_time and end_time:
            params["FilterExpression"] = "#ts BETWEEN :start AND :end"
            params["ExpressionAttributeNames"] = {"#ts": "timestamp"}
            params["ExpressionAttributeValues"][":start"] = start_time.isoformat()
            params["ExpressionAttributeValues"][":end"] = end_time.isoformat()

        return params

    def _item_to_event(self, item: dict[str, Any]) -> AuditEvent:
        """Convert DynamoDB item to AuditEvent."""
        return AuditEvent(
            event_id=item["event_id"],
            event_type=AuditEventType(item["event_type"]),
            timestamp=datetime.fromisoformat(item["timestamp"]),
            tenant_id=item.get("tenant_id"),
            user_id=item.get("user_id"),
            source_ip=item.get("source_ip"),
            user_agent=item.get("user_agent"),
            resource=item.get("resource"),
            action=item.get("action"),
            result=item.get("result"),
            details=item.get("details", {}),
            request_id=item.get("request_id"),
        )

    def _is_critical_event(self, event_type: AuditEventType) -> bool:
        """Check if event type is critical and requires alerting."""
        critical_types = {
            AuditEventType.LOGIN_FAILURE,
            AuditEventType.ACCESS_DENIED,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.SECRET_ACCESS,
            AuditEventType.CONFIG_CHANGE,
        }
        return event_type in critical_types

    def _send_alert(self, event: AuditEvent) -> None:
        """Send alert for critical audit event."""
        if not settings.alert_topic_arn:
            return

        try:
            self._clients.sns.publish(
                TopicArn=settings.alert_topic_arn,
                Subject=f"Audit Alert: {event.event_type.value}",
                Message=json_dumps({
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "tenant_id": event.tenant_id,
                    "user_id": event.user_id,
                    "resource": event.resource,
                    "action": event.action,
                    "result": event.result,
                }),
            )
        except Exception as e:
            logger.error(f"Failed to send audit alert: {e}")
