"""Tenant Service for multi-tenant operations.

Handles tenant CRUD, configuration, and isolation.
"""

from datetime import datetime, timezone
from typing import Any

from aws_lambda_powertools import Logger, Tracer

from src.common.clients import get_aws_clients, get_dynamodb_table
from src.common.config import get_settings
from src.common.exceptions import (
    ResourceNotFoundError,
    TenantError,
    ValidationError,
)
from src.common.models import TenantInfo, TenantStatus, TenantTier
from src.common.utils import generate_id, utc_now

logger = Logger()
tracer = Tracer()

settings = get_settings()


class TenantService:
    """Service for managing tenants in a multi-tenant system."""

    def __init__(self) -> None:
        self._clients = get_aws_clients()
        self._table_name = settings.tenant_table

    @property
    def _table(self) -> Any:
        """Get DynamoDB table resource."""
        return get_dynamodb_table(self._table_name)

    @tracer.capture_method
    def create_tenant(
        self,
        name: str,
        tier: TenantTier = TenantTier.FREE,
        settings_dict: dict[str, Any] | None = None,
    ) -> TenantInfo:
        """Create a new tenant.

        Args:
            name: Tenant name
            tier: Subscription tier
            settings_dict: Optional tenant settings

        Returns:
            Created tenant info

        Raises:
            ValidationError: If tenant name is invalid
        """
        if not name or len(name) < 2:
            raise ValidationError("Tenant name must be at least 2 characters")

        tenant_id = generate_id("tenant-")
        now = utc_now()

        tenant = TenantInfo(
            tenant_id=tenant_id,
            name=name,
            status=TenantStatus.PENDING,
            tier=tier,
            created_at=now,
            settings=settings_dict or {},
        )

        item = {
            "PK": f"TENANT#{tenant_id}",
            "SK": "METADATA",
            "tenant_id": tenant_id,
            "name": name,
            "status": tenant.status.value,
            "tier": tenant.tier.value,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "settings": tenant.settings,
            "GSI1PK": "TENANT",
            "GSI1SK": f"{tenant.status.value}#{now.isoformat()}",
        }

        self._table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(PK)",
        )

        logger.info(f"Created tenant: {tenant_id}")

        # Publish event for async processing
        self._publish_event("TenantCreated", tenant)

        return tenant

    @tracer.capture_method
    def get_tenant(self, tenant_id: str) -> TenantInfo:
        """Get tenant by ID.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant info

        Raises:
            ResourceNotFoundError: If tenant not found
        """
        response = self._table.get_item(
            Key={"PK": f"TENANT#{tenant_id}", "SK": "METADATA"}
        )

        item = response.get("Item")
        if not item:
            raise ResourceNotFoundError("Tenant", tenant_id)

        return self._item_to_tenant(item)

    @tracer.capture_method
    def update_tenant(
        self,
        tenant_id: str,
        name: str | None = None,
        tier: TenantTier | None = None,
        settings_dict: dict[str, Any] | None = None,
    ) -> TenantInfo:
        """Update tenant information.

        Args:
            tenant_id: Tenant ID
            name: Optional new name
            tier: Optional new tier
            settings_dict: Optional settings to merge

        Returns:
            Updated tenant info
        """
        # Build update expression
        update_parts = ["#updated_at = :updated_at"]
        names = {"#updated_at": "updated_at"}
        values: dict[str, Any] = {":updated_at": utc_now().isoformat()}

        if name:
            update_parts.append("#name = :name")
            names["#name"] = "name"
            values[":name"] = name

        if tier:
            update_parts.append("#tier = :tier")
            names["#tier"] = "tier"
            values[":tier"] = tier.value

        if settings_dict:
            update_parts.append("#settings = :settings")
            names["#settings"] = "settings"
            values[":settings"] = settings_dict

        response = self._table.update_item(
            Key={"PK": f"TENANT#{tenant_id}", "SK": "METADATA"},
            UpdateExpression=f"SET {', '.join(update_parts)}",
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ReturnValues="ALL_NEW",
            ConditionExpression="attribute_exists(PK)",
        )

        tenant = self._item_to_tenant(response["Attributes"])
        logger.info(f"Updated tenant: {tenant_id}")

        self._publish_event("TenantUpdated", tenant)

        return tenant

    @tracer.capture_method
    def activate_tenant(self, tenant_id: str) -> TenantInfo:
        """Activate a pending tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Updated tenant info
        """
        return self._update_status(tenant_id, TenantStatus.ACTIVE)

    @tracer.capture_method
    def suspend_tenant(self, tenant_id: str, reason: str | None = None) -> TenantInfo:
        """Suspend a tenant.

        Args:
            tenant_id: Tenant ID
            reason: Optional suspension reason

        Returns:
            Updated tenant info
        """
        tenant = self._update_status(tenant_id, TenantStatus.SUSPENDED)

        if reason:
            # Store suspension reason
            self._table.update_item(
                Key={"PK": f"TENANT#{tenant_id}", "SK": "METADATA"},
                UpdateExpression="SET suspension_reason = :reason",
                ExpressionAttributeValues={":reason": reason},
            )

        return tenant

    @tracer.capture_method
    def delete_tenant(self, tenant_id: str, soft_delete: bool = True) -> None:
        """Delete a tenant.

        Args:
            tenant_id: Tenant ID
            soft_delete: If True, mark as deleted; if False, hard delete
        """
        if soft_delete:
            self._update_status(tenant_id, TenantStatus.DELETED)
        else:
            # Hard delete - remove all tenant data
            self._table.delete_item(
                Key={"PK": f"TENANT#{tenant_id}", "SK": "METADATA"}
            )
            # TODO: Delete all tenant resources

        logger.info(f"Deleted tenant: {tenant_id} (soft={soft_delete})")

        self._clients.events.put_events(
            Entries=[
                {
                    "Source": "enterprise-api",
                    "DetailType": "TenantDeleted",
                    "Detail": f'{{"tenant_id": "{tenant_id}", "soft_delete": {str(soft_delete).lower()}}}',
                    "EventBusName": settings.event_bus_name,
                }
            ]
        )

    @tracer.capture_method
    def list_tenants(
        self,
        status: TenantStatus | None = None,
        limit: int = 50,
        last_key: str | None = None,
    ) -> tuple[list[TenantInfo], str | None]:
        """List tenants with optional filtering.

        Args:
            status: Optional status filter
            limit: Maximum number of results
            last_key: Pagination token

        Returns:
            Tuple of (tenants list, next page token)
        """
        params: dict[str, Any] = {
            "IndexName": "GSI1",
            "KeyConditionExpression": "GSI1PK = :pk",
            "ExpressionAttributeValues": {":pk": "TENANT"},
            "Limit": limit,
            "ScanIndexForward": False,  # Newest first
        }

        if status:
            params["KeyConditionExpression"] += " AND begins_with(GSI1SK, :status)"
            params["ExpressionAttributeValues"][":status"] = status.value

        if last_key:
            import json
            params["ExclusiveStartKey"] = json.loads(last_key)

        response = self._table.query(**params)

        tenants = [self._item_to_tenant(item) for item in response.get("Items", [])]

        next_key = None
        if "LastEvaluatedKey" in response:
            import json
            next_key = json.dumps(response["LastEvaluatedKey"])

        return tenants, next_key

    @tracer.capture_method
    def get_tenant_settings(self, tenant_id: str) -> dict[str, Any]:
        """Get tenant settings.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant settings dictionary
        """
        tenant = self.get_tenant(tenant_id)
        return tenant.settings

    @tracer.capture_method
    def update_tenant_settings(
        self,
        tenant_id: str,
        settings_updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Update tenant settings (merge).

        Args:
            tenant_id: Tenant ID
            settings_updates: Settings to merge

        Returns:
            Updated settings
        """
        # Get current settings
        current = self.get_tenant_settings(tenant_id)
        current.update(settings_updates)

        # Save merged settings
        self._table.update_item(
            Key={"PK": f"TENANT#{tenant_id}", "SK": "METADATA"},
            UpdateExpression="SET #settings = :settings, #updated_at = :updated_at",
            ExpressionAttributeNames={
                "#settings": "settings",
                "#updated_at": "updated_at",
            },
            ExpressionAttributeValues={
                ":settings": current,
                ":updated_at": utc_now().isoformat(),
            },
        )

        return current

    def _update_status(self, tenant_id: str, status: TenantStatus) -> TenantInfo:
        """Update tenant status.

        Args:
            tenant_id: Tenant ID
            status: New status

        Returns:
            Updated tenant info
        """
        now = utc_now()

        response = self._table.update_item(
            Key={"PK": f"TENANT#{tenant_id}", "SK": "METADATA"},
            UpdateExpression="SET #status = :status, #updated_at = :updated_at, GSI1SK = :gsi1sk",
            ExpressionAttributeNames={
                "#status": "status",
                "#updated_at": "updated_at",
            },
            ExpressionAttributeValues={
                ":status": status.value,
                ":updated_at": now.isoformat(),
                ":gsi1sk": f"{status.value}#{now.isoformat()}",
            },
            ReturnValues="ALL_NEW",
            ConditionExpression="attribute_exists(PK)",
        )

        return self._item_to_tenant(response["Attributes"])

    def _item_to_tenant(self, item: dict[str, Any]) -> TenantInfo:
        """Convert DynamoDB item to TenantInfo.

        Args:
            item: DynamoDB item

        Returns:
            TenantInfo instance
        """
        return TenantInfo(
            tenant_id=item["tenant_id"],
            name=item["name"],
            status=TenantStatus(item["status"]),
            tier=TenantTier(item.get("tier", "free")),
            created_at=datetime.fromisoformat(item["created_at"]),
            settings=item.get("settings", {}),
        )

    def _publish_event(self, event_type: str, tenant: TenantInfo) -> None:
        """Publish tenant event to EventBridge.

        Args:
            event_type: Event type (TenantCreated, TenantUpdated, etc.)
            tenant: Tenant info
        """
        try:
            import json

            self._clients.events.put_events(
                Entries=[
                    {
                        "Source": "enterprise-api",
                        "DetailType": event_type,
                        "Detail": json.dumps({
                            "tenant_id": tenant.tenant_id,
                            "name": tenant.name,
                            "status": tenant.status.value,
                            "tier": tenant.tier.value,
                        }),
                        "EventBusName": settings.event_bus_name,
                    }
                ]
            )
        except Exception as e:
            logger.warning(f"Failed to publish event: {e}")
