"""CRM integration service for multi-tenant SaaS platform.

This service handles:
- CRM connection management (Salesforce, HubSpot, Dynamics 365)
- Contact synchronization
- Deal/Opportunity management
- Activity logging
- Email-to-CRM activity creation
"""

import json
import uuid
from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger, Tracer

from src.common.clients import AWSClients
from src.common.config import get_settings
from src.common.models import (
    CRMActivity,
    CRMConnection,
    CRMConnectionStatus,
    CRMContact,
    CRMDeal,
    CRMProvider,
    EmailMessage,
    TenantCRMSettings,
)

logger = Logger()
tracer = Tracer()


class CRMService:
    """Service for CRM integrations and data synchronization."""

    def __init__(self, clients: AWSClients | None = None):
        """Initialize CRM service."""
        self.settings = get_settings()
        self.clients = clients or AWSClients()
        self._connections_table = f"{self.settings.project_name}-{self.settings.environment}-crm-connections"
        self._contacts_table = f"{self.settings.project_name}-{self.settings.environment}-crm-contacts"
        self._deals_table = f"{self.settings.project_name}-{self.settings.environment}-crm-deals"
        self._activities_table = f"{self.settings.project_name}-{self.settings.environment}-crm-activities"

    # =========================================================================
    # CRM Connection Management
    # =========================================================================

    @tracer.capture_method
    def create_connection(
        self,
        tenant_id: str,
        provider: CRMProvider,
        instance_url: str | None = None,
        organization_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CRMConnection:
        """Create a new CRM connection for a tenant."""
        connection = CRMConnection(
            connection_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            provider=provider,
            instance_url=instance_url,
            organization_id=organization_id,
            status=CRMConnectionStatus.PENDING,
            metadata=metadata or {},
        )

        self.clients.dynamodb.put_item(
            TableName=self._connections_table,
            Item=self._connection_to_item(connection),
        )

        logger.info(
            "CRM connection created",
            extra={
                "tenant_id": tenant_id,
                "connection_id": connection.connection_id,
                "provider": provider.value,
            },
        )

        return connection

    @tracer.capture_method
    def get_connection(self, tenant_id: str, connection_id: str) -> CRMConnection | None:
        """Get a CRM connection by ID."""
        response = self.clients.dynamodb.get_item(
            TableName=self._connections_table,
            Key={
                "pk": {"S": f"TENANT#{tenant_id}"},
                "sk": {"S": f"CONNECTION#{connection_id}"},
            },
        )

        item = response.get("Item")
        if not item:
            return None

        return self._item_to_connection(item)

    @tracer.capture_method
    def list_connections(self, tenant_id: str) -> list[CRMConnection]:
        """List all CRM connections for a tenant."""
        response = self.clients.dynamodb.query(
            TableName=self._connections_table,
            KeyConditionExpression="pk = :pk AND begins_with(sk, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"TENANT#{tenant_id}"},
                ":sk_prefix": {"S": "CONNECTION#"},
            },
        )

        return [self._item_to_connection(item) for item in response.get("Items", [])]

    @tracer.capture_method
    def update_connection_status(
        self,
        tenant_id: str,
        connection_id: str,
        status: CRMConnectionStatus,
        token_expires_at: datetime | None = None,
    ) -> CRMConnection | None:
        """Update CRM connection status."""
        update_expr = "SET #status = :status, updated_at = :updated_at"
        expr_values: dict[str, Any] = {
            ":status": {"S": status.value},
            ":updated_at": {"S": datetime.utcnow().isoformat()},
        }

        if token_expires_at:
            update_expr += ", token_expires_at = :token_expires"
            expr_values[":token_expires"] = {"S": token_expires_at.isoformat()}

        self.clients.dynamodb.update_item(
            TableName=self._connections_table,
            Key={
                "pk": {"S": f"TENANT#{tenant_id}"},
                "sk": {"S": f"CONNECTION#{connection_id}"},
            },
            UpdateExpression=update_expr,
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues=expr_values,
        )

        return self.get_connection(tenant_id, connection_id)

    # =========================================================================
    # Contact Management
    # =========================================================================

    @tracer.capture_method
    def upsert_contact(self, contact: CRMContact) -> CRMContact:
        """Create or update a contact."""
        self.clients.dynamodb.put_item(
            TableName=self._contacts_table,
            Item=self._contact_to_item(contact),
        )
        return contact

    @tracer.capture_method
    def get_contact(self, tenant_id: str, contact_id: str) -> CRMContact | None:
        """Get a contact by ID."""
        response = self.clients.dynamodb.get_item(
            TableName=self._contacts_table,
            Key={
                "pk": {"S": f"TENANT#{tenant_id}"},
                "sk": {"S": f"CONTACT#{contact_id}"},
            },
        )

        item = response.get("Item")
        if not item:
            return None

        return self._item_to_contact(item)

    @tracer.capture_method
    def get_contact_by_email(
        self, tenant_id: str, email: str
    ) -> CRMContact | None:
        """Get a contact by email address."""
        response = self.clients.dynamodb.query(
            TableName=self._contacts_table,
            IndexName="email-index",
            KeyConditionExpression="tenant_id = :tid AND email = :email",
            ExpressionAttributeValues={
                ":tid": {"S": tenant_id},
                ":email": {"S": email.lower()},
            },
            Limit=1,
        )

        items = response.get("Items", [])
        if not items:
            return None

        return self._item_to_contact(items[0])

    @tracer.capture_method
    def list_contacts(
        self,
        tenant_id: str,
        connection_id: str | None = None,
        limit: int = 100,
    ) -> list[CRMContact]:
        """List contacts for a tenant."""
        if connection_id:
            # Use connection index
            response = self.clients.dynamodb.query(
                TableName=self._contacts_table,
                IndexName="connection-index",
                KeyConditionExpression="connection_id = :cid",
                ExpressionAttributeValues={":cid": {"S": connection_id}},
                Limit=limit,
            )
        else:
            response = self.clients.dynamodb.query(
                TableName=self._contacts_table,
                KeyConditionExpression="pk = :pk",
                ExpressionAttributeValues={":pk": {"S": f"TENANT#{tenant_id}"}},
                Limit=limit,
            )

        return [self._item_to_contact(item) for item in response.get("Items", [])]

    @tracer.capture_method
    def update_contact_score(
        self,
        tenant_id: str,
        contact_id: str,
        lead_score: float,
        lifecycle_stage: str | None = None,
    ) -> CRMContact | None:
        """Update contact lead score and lifecycle stage."""
        update_expr = "SET lead_score = :score, synced_at = :synced"
        expr_values: dict[str, Any] = {
            ":score": {"N": str(lead_score)},
            ":synced": {"S": datetime.utcnow().isoformat()},
        }

        if lifecycle_stage:
            update_expr += ", lifecycle_stage = :stage"
            expr_values[":stage"] = {"S": lifecycle_stage}

        self.clients.dynamodb.update_item(
            TableName=self._contacts_table,
            Key={
                "pk": {"S": f"TENANT#{tenant_id}"},
                "sk": {"S": f"CONTACT#{contact_id}"},
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
        )

        return self.get_contact(tenant_id, contact_id)

    # =========================================================================
    # Deal Management
    # =========================================================================

    @tracer.capture_method
    def upsert_deal(self, deal: CRMDeal) -> CRMDeal:
        """Create or update a deal."""
        self.clients.dynamodb.put_item(
            TableName=self._deals_table,
            Item=self._deal_to_item(deal),
        )
        return deal

    @tracer.capture_method
    def get_deal(self, tenant_id: str, deal_id: str) -> CRMDeal | None:
        """Get a deal by ID."""
        response = self.clients.dynamodb.get_item(
            TableName=self._deals_table,
            Key={
                "pk": {"S": f"TENANT#{tenant_id}"},
                "sk": {"S": f"DEAL#{deal_id}"},
            },
        )

        item = response.get("Item")
        if not item:
            return None

        return self._item_to_deal(item)

    @tracer.capture_method
    def list_deals(
        self,
        tenant_id: str,
        stage: str | None = None,
        limit: int = 100,
    ) -> list[CRMDeal]:
        """List deals for a tenant."""
        response = self.clients.dynamodb.query(
            TableName=self._deals_table,
            KeyConditionExpression="pk = :pk",
            ExpressionAttributeValues={":pk": {"S": f"TENANT#{tenant_id}"}},
            Limit=limit,
        )

        deals = [self._item_to_deal(item) for item in response.get("Items", [])]

        if stage:
            deals = [d for d in deals if d.stage == stage]

        return deals

    # =========================================================================
    # Activity Management
    # =========================================================================

    @tracer.capture_method
    def create_activity(self, activity: CRMActivity) -> CRMActivity:
        """Create a new activity."""
        self.clients.dynamodb.put_item(
            TableName=self._activities_table,
            Item=self._activity_to_item(activity),
        )

        logger.info(
            "Activity created",
            extra={
                "tenant_id": activity.tenant_id,
                "activity_id": activity.activity_id,
                "activity_type": activity.activity_type,
            },
        )

        return activity

    @tracer.capture_method
    def create_activity_from_email(
        self,
        email: EmailMessage,
        settings: TenantCRMSettings,
    ) -> CRMActivity | None:
        """Create a CRM activity from an email message."""
        if not settings.create_activities_from_emails:
            return None

        # Find or create contact for sender
        contact = self.get_contact_by_email(email.tenant_id, email.sender)
        contact_ids = [contact.contact_id] if contact else []

        activity = CRMActivity(
            activity_id=str(uuid.uuid4()),
            tenant_id=email.tenant_id,
            connection_id=email.connection_id,
            external_id=email.message_id,
            activity_type="email",
            subject=email.subject,
            description=email.summary or email.body_preview,
            contact_ids=contact_ids,
            completed_at=email.received_at,
            status="completed",
        )

        return self.create_activity(activity)

    @tracer.capture_method
    def list_activities(
        self,
        tenant_id: str,
        contact_id: str | None = None,
        deal_id: str | None = None,
        limit: int = 50,
    ) -> list[CRMActivity]:
        """List activities for a tenant, optionally filtered by contact or deal."""
        response = self.clients.dynamodb.query(
            TableName=self._activities_table,
            KeyConditionExpression="pk = :pk",
            ExpressionAttributeValues={":pk": {"S": f"TENANT#{tenant_id}"}},
            Limit=limit,
            ScanIndexForward=False,  # Newest first
        )

        activities = [
            self._item_to_activity(item) for item in response.get("Items", [])
        ]

        # Filter by contact or deal if specified
        if contact_id:
            activities = [a for a in activities if contact_id in a.contact_ids]
        if deal_id:
            activities = [a for a in activities if deal_id in a.deal_ids]

        return activities

    # =========================================================================
    # CRM Synchronization
    # =========================================================================

    @tracer.capture_method
    def sync_contacts(
        self,
        tenant_id: str,
        connection_id: str,
        settings: TenantCRMSettings,
    ) -> int:
        """Sync contacts from CRM provider."""
        connection = self.get_connection(tenant_id, connection_id)
        if not connection or connection.status != CRMConnectionStatus.CONNECTED:
            return 0

        # Fetch contacts from provider (mock implementation)
        contacts_data = self._fetch_contacts_from_provider(connection)

        synced_count = 0
        for contact_data in contacts_data:
            contact = self._create_contact_from_provider_data(
                tenant_id, connection_id, contact_data
            )
            self.upsert_contact(contact)
            synced_count += 1

        # Update last sync time
        self._update_sync_time(tenant_id, connection_id)

        logger.info(
            "Contact sync completed",
            extra={
                "tenant_id": tenant_id,
                "connection_id": connection_id,
                "synced_count": synced_count,
            },
        )

        return synced_count

    @tracer.capture_method
    def sync_deals(
        self,
        tenant_id: str,
        connection_id: str,
        settings: TenantCRMSettings,
    ) -> int:
        """Sync deals from CRM provider."""
        connection = self.get_connection(tenant_id, connection_id)
        if not connection or connection.status != CRMConnectionStatus.CONNECTED:
            return 0

        # Fetch deals from provider (mock implementation)
        deals_data = self._fetch_deals_from_provider(connection)

        synced_count = 0
        for deal_data in deals_data:
            deal = self._create_deal_from_provider_data(
                tenant_id, connection_id, deal_data
            )
            self.upsert_deal(deal)
            synced_count += 1

        logger.info(
            "Deal sync completed",
            extra={
                "tenant_id": tenant_id,
                "connection_id": connection_id,
                "synced_count": synced_count,
            },
        )

        return synced_count

    def _fetch_contacts_from_provider(
        self, connection: CRMConnection
    ) -> list[dict[str, Any]]:
        """Fetch contacts from CRM provider (mock implementation)."""
        # In real implementation, this would call:
        # - Salesforce REST API
        # - HubSpot API
        # - Dynamics 365 API
        return []

    def _fetch_deals_from_provider(
        self, connection: CRMConnection
    ) -> list[dict[str, Any]]:
        """Fetch deals from CRM provider (mock implementation)."""
        return []

    def _create_contact_from_provider_data(
        self,
        tenant_id: str,
        connection_id: str,
        data: dict[str, Any],
    ) -> CRMContact:
        """Create CRMContact from provider data."""
        return CRMContact(
            contact_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            connection_id=connection_id,
            external_id=data.get("id", ""),
            email=data.get("email", "").lower(),
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            company=data.get("company"),
            title=data.get("title"),
            phone=data.get("phone"),
            lifecycle_stage=data.get("lifecycleStage"),
            owner_id=data.get("ownerId"),
            tags=data.get("tags", []),
            custom_fields=data.get("customFields", {}),
        )

    def _create_deal_from_provider_data(
        self,
        tenant_id: str,
        connection_id: str,
        data: dict[str, Any],
    ) -> CRMDeal:
        """Create CRMDeal from provider data."""
        return CRMDeal(
            deal_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            connection_id=connection_id,
            external_id=data.get("id", ""),
            name=data.get("name", ""),
            amount=data.get("amount"),
            currency=data.get("currency", "USD"),
            stage=data.get("stage", ""),
            probability=data.get("probability"),
            owner_id=data.get("ownerId"),
            pipeline_id=data.get("pipelineId"),
            custom_fields=data.get("customFields", {}),
        )

    def _update_sync_time(self, tenant_id: str, connection_id: str) -> None:
        """Update last sync timestamp for a connection."""
        self.clients.dynamodb.update_item(
            TableName=self._connections_table,
            Key={
                "pk": {"S": f"TENANT#{tenant_id}"},
                "sk": {"S": f"CONNECTION#{connection_id}"},
            },
            UpdateExpression="SET last_sync_at = :sync_at",
            ExpressionAttributeValues={
                ":sync_at": {"S": datetime.utcnow().isoformat()},
            },
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _connection_to_item(self, conn: CRMConnection) -> dict[str, Any]:
        """Convert CRMConnection to DynamoDB item."""
        item = {
            "pk": {"S": f"TENANT#{conn.tenant_id}"},
            "sk": {"S": f"CONNECTION#{conn.connection_id}"},
            "connection_id": {"S": conn.connection_id},
            "tenant_id": {"S": conn.tenant_id},
            "provider": {"S": conn.provider.value},
            "status": {"S": conn.status.value},
            "sync_enabled": {"BOOL": conn.sync_enabled},
            "sync_direction": {"S": conn.sync_direction},
            "created_at": {"S": conn.created_at.isoformat()},
            "updated_at": {"S": conn.updated_at.isoformat()},
            "metadata": {"S": json.dumps(conn.metadata)},
        }

        if conn.instance_url:
            item["instance_url"] = {"S": conn.instance_url}
        if conn.organization_id:
            item["organization_id"] = {"S": conn.organization_id}
        if conn.scopes:
            item["scopes"] = {"SS": conn.scopes}

        return item

    def _item_to_connection(self, item: dict[str, Any]) -> CRMConnection:
        """Convert DynamoDB item to CRMConnection."""
        return CRMConnection(
            connection_id=item["connection_id"]["S"],
            tenant_id=item["tenant_id"]["S"],
            provider=CRMProvider(item["provider"]["S"]),
            status=CRMConnectionStatus(item["status"]["S"]),
            instance_url=item.get("instance_url", {}).get("S"),
            organization_id=item.get("organization_id", {}).get("S"),
            scopes=list(item.get("scopes", {}).get("SS", [])),
            sync_enabled=item.get("sync_enabled", {}).get("BOOL", True),
            sync_direction=item.get("sync_direction", {}).get("S", "bidirectional"),
            created_at=datetime.fromisoformat(item["created_at"]["S"]),
            updated_at=datetime.fromisoformat(item["updated_at"]["S"]),
            metadata=json.loads(item.get("metadata", {}).get("S", "{}")),
        )

    def _contact_to_item(self, contact: CRMContact) -> dict[str, Any]:
        """Convert CRMContact to DynamoDB item."""
        item = {
            "pk": {"S": f"TENANT#{contact.tenant_id}"},
            "sk": {"S": f"CONTACT#{contact.contact_id}"},
            "contact_id": {"S": contact.contact_id},
            "tenant_id": {"S": contact.tenant_id},
            "connection_id": {"S": contact.connection_id},
            "external_id": {"S": contact.external_id},
            "email": {"S": contact.email.lower()},
            "synced_at": {"S": contact.synced_at.isoformat()},
        }

        if contact.first_name:
            item["first_name"] = {"S": contact.first_name}
        if contact.last_name:
            item["last_name"] = {"S": contact.last_name}
        if contact.company:
            item["company"] = {"S": contact.company}
        if contact.title:
            item["title"] = {"S": contact.title}
        if contact.phone:
            item["phone"] = {"S": contact.phone}
        if contact.lead_score is not None:
            item["lead_score"] = {"N": str(contact.lead_score)}
        if contact.lifecycle_stage:
            item["lifecycle_stage"] = {"S": contact.lifecycle_stage}
        if contact.owner_id:
            item["owner_id"] = {"S": contact.owner_id}
        if contact.tags:
            item["tags"] = {"SS": contact.tags}
        if contact.custom_fields:
            item["custom_fields"] = {"S": json.dumps(contact.custom_fields)}

        return item

    def _item_to_contact(self, item: dict[str, Any]) -> CRMContact:
        """Convert DynamoDB item to CRMContact."""
        return CRMContact(
            contact_id=item["contact_id"]["S"],
            tenant_id=item["tenant_id"]["S"],
            connection_id=item["connection_id"]["S"],
            external_id=item["external_id"]["S"],
            email=item["email"]["S"],
            first_name=item.get("first_name", {}).get("S"),
            last_name=item.get("last_name", {}).get("S"),
            company=item.get("company", {}).get("S"),
            title=item.get("title", {}).get("S"),
            phone=item.get("phone", {}).get("S"),
            lead_score=float(item["lead_score"]["N"])
            if "lead_score" in item
            else None,
            lifecycle_stage=item.get("lifecycle_stage", {}).get("S"),
            owner_id=item.get("owner_id", {}).get("S"),
            tags=list(item.get("tags", {}).get("SS", [])),
            custom_fields=json.loads(item.get("custom_fields", {}).get("S", "{}")),
            synced_at=datetime.fromisoformat(item["synced_at"]["S"]),
        )

    def _deal_to_item(self, deal: CRMDeal) -> dict[str, Any]:
        """Convert CRMDeal to DynamoDB item."""
        item = {
            "pk": {"S": f"TENANT#{deal.tenant_id}"},
            "sk": {"S": f"DEAL#{deal.deal_id}"},
            "deal_id": {"S": deal.deal_id},
            "tenant_id": {"S": deal.tenant_id},
            "connection_id": {"S": deal.connection_id},
            "external_id": {"S": deal.external_id},
            "name": {"S": deal.name},
            "stage": {"S": deal.stage},
            "currency": {"S": deal.currency},
            "created_at": {"S": deal.created_at.isoformat()},
            "updated_at": {"S": deal.updated_at.isoformat()},
            "synced_at": {"S": deal.synced_at.isoformat()},
        }

        if deal.amount is not None:
            item["amount"] = {"N": str(deal.amount)}
        if deal.probability is not None:
            item["probability"] = {"N": str(deal.probability)}
        if deal.close_date:
            item["close_date"] = {"S": deal.close_date.isoformat()}
        if deal.contact_ids:
            item["contact_ids"] = {"SS": deal.contact_ids}
        if deal.owner_id:
            item["owner_id"] = {"S": deal.owner_id}
        if deal.pipeline_id:
            item["pipeline_id"] = {"S": deal.pipeline_id}
        if deal.custom_fields:
            item["custom_fields"] = {"S": json.dumps(deal.custom_fields)}

        return item

    def _item_to_deal(self, item: dict[str, Any]) -> CRMDeal:
        """Convert DynamoDB item to CRMDeal."""
        return CRMDeal(
            deal_id=item["deal_id"]["S"],
            tenant_id=item["tenant_id"]["S"],
            connection_id=item["connection_id"]["S"],
            external_id=item["external_id"]["S"],
            name=item["name"]["S"],
            stage=item["stage"]["S"],
            currency=item.get("currency", {}).get("S", "USD"),
            amount=float(item["amount"]["N"]) if "amount" in item else None,
            probability=float(item["probability"]["N"])
            if "probability" in item
            else None,
            close_date=datetime.fromisoformat(item["close_date"]["S"])
            if "close_date" in item
            else None,
            contact_ids=list(item.get("contact_ids", {}).get("SS", [])),
            owner_id=item.get("owner_id", {}).get("S"),
            pipeline_id=item.get("pipeline_id", {}).get("S"),
            custom_fields=json.loads(item.get("custom_fields", {}).get("S", "{}")),
            created_at=datetime.fromisoformat(item["created_at"]["S"]),
            updated_at=datetime.fromisoformat(item["updated_at"]["S"]),
            synced_at=datetime.fromisoformat(item["synced_at"]["S"]),
        )

    def _activity_to_item(self, activity: CRMActivity) -> dict[str, Any]:
        """Convert CRMActivity to DynamoDB item."""
        item = {
            "pk": {"S": f"TENANT#{activity.tenant_id}"},
            "sk": {"S": f"ACTIVITY#{activity.activity_id}"},
            "activity_id": {"S": activity.activity_id},
            "tenant_id": {"S": activity.tenant_id},
            "connection_id": {"S": activity.connection_id},
            "external_id": {"S": activity.external_id},
            "activity_type": {"S": activity.activity_type},
            "subject": {"S": activity.subject},
            "status": {"S": activity.status},
            "created_at": {"S": activity.created_at.isoformat()},
            "synced_at": {"S": activity.synced_at.isoformat()},
        }

        if activity.description:
            item["description"] = {"S": activity.description}
        if activity.contact_ids:
            item["contact_ids"] = {"SS": activity.contact_ids}
        if activity.deal_ids:
            item["deal_ids"] = {"SS": activity.deal_ids}
        if activity.owner_id:
            item["owner_id"] = {"S": activity.owner_id}
        if activity.due_date:
            item["due_date"] = {"S": activity.due_date.isoformat()}
        if activity.completed_at:
            item["completed_at"] = {"S": activity.completed_at.isoformat()}
        if activity.outcome:
            item["outcome"] = {"S": activity.outcome}
        if activity.duration_minutes is not None:
            item["duration_minutes"] = {"N": str(activity.duration_minutes)}

        return item

    def _item_to_activity(self, item: dict[str, Any]) -> CRMActivity:
        """Convert DynamoDB item to CRMActivity."""
        return CRMActivity(
            activity_id=item["activity_id"]["S"],
            tenant_id=item["tenant_id"]["S"],
            connection_id=item["connection_id"]["S"],
            external_id=item["external_id"]["S"],
            activity_type=item["activity_type"]["S"],
            subject=item["subject"]["S"],
            description=item.get("description", {}).get("S"),
            contact_ids=list(item.get("contact_ids", {}).get("SS", [])),
            deal_ids=list(item.get("deal_ids", {}).get("SS", [])),
            owner_id=item.get("owner_id", {}).get("S"),
            due_date=datetime.fromisoformat(item["due_date"]["S"])
            if "due_date" in item
            else None,
            completed_at=datetime.fromisoformat(item["completed_at"]["S"])
            if "completed_at" in item
            else None,
            status=item.get("status", {}).get("S", "pending"),
            outcome=item.get("outcome", {}).get("S"),
            duration_minutes=int(item["duration_minutes"]["N"])
            if "duration_minutes" in item
            else None,
            created_at=datetime.fromisoformat(item["created_at"]["S"]),
            synced_at=datetime.fromisoformat(item["synced_at"]["S"]),
        )
