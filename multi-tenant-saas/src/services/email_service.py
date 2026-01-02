"""Email processing service for multi-tenant SaaS platform.

This service handles:
- Email connection management (Microsoft 365, Google Workspace)
- Email synchronization
- GenAI-powered email analysis (sentiment, intent, action items)
- Email-to-CRM activity creation
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from aws_lambda_powertools import Logger, Tracer

from src.common.clients import AWSClients
from src.common.config import get_settings
from src.common.models import (
    AnalysisType,
    EmailConnection,
    EmailConnectionStatus,
    EmailMessage,
    EmailProcessingJob,
    EmailProvider,
    GenAIAnalysisRequest,
    GenAIAnalysisResult,
    TenantEmailSettings,
)

logger = Logger()
tracer = Tracer()


class EmailService:
    """Service for email processing and GenAI analysis."""

    def __init__(self, clients: AWSClients | None = None):
        """Initialize email service."""
        self.settings = get_settings()
        self.clients = clients or AWSClients()
        self._connections_table = f"{self.settings.project_name}-{self.settings.environment}-email-connections"
        self._messages_table = f"{self.settings.project_name}-{self.settings.environment}-email-messages"
        self._jobs_table = f"{self.settings.project_name}-{self.settings.environment}-email-jobs"

    # =========================================================================
    # Email Connection Management
    # =========================================================================

    @tracer.capture_method
    def create_connection(
        self,
        tenant_id: str,
        provider: EmailProvider,
        email_address: str,
        display_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EmailConnection:
        """Create a new email connection for a tenant."""
        connection = EmailConnection(
            connection_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            provider=provider,
            email_address=email_address,
            display_name=display_name,
            status=EmailConnectionStatus.PENDING,
            metadata=metadata or {},
        )

        self.clients.dynamodb.put_item(
            TableName=self._connections_table,
            Item=self._connection_to_item(connection),
        )

        logger.info(
            "Email connection created",
            extra={
                "tenant_id": tenant_id,
                "connection_id": connection.connection_id,
                "provider": provider.value,
            },
        )

        return connection

    @tracer.capture_method
    def get_connection(self, tenant_id: str, connection_id: str) -> EmailConnection | None:
        """Get an email connection by ID."""
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
    def list_connections(self, tenant_id: str) -> list[EmailConnection]:
        """List all email connections for a tenant."""
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
        status: EmailConnectionStatus,
        token_expires_at: datetime | None = None,
    ) -> EmailConnection | None:
        """Update email connection status."""
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

    @tracer.capture_method
    def delete_connection(self, tenant_id: str, connection_id: str) -> bool:
        """Delete an email connection."""
        self.clients.dynamodb.delete_item(
            TableName=self._connections_table,
            Key={
                "pk": {"S": f"TENANT#{tenant_id}"},
                "sk": {"S": f"CONNECTION#{connection_id}"},
            },
        )
        return True

    # =========================================================================
    # Email Message Management
    # =========================================================================

    @tracer.capture_method
    def store_message(self, message: EmailMessage) -> EmailMessage:
        """Store a processed email message."""
        self.clients.dynamodb.put_item(
            TableName=self._messages_table,
            Item=self._message_to_item(message),
        )
        return message

    @tracer.capture_method
    def get_message(self, tenant_id: str, message_id: str) -> EmailMessage | None:
        """Get an email message by ID."""
        response = self.clients.dynamodb.get_item(
            TableName=self._messages_table,
            Key={
                "pk": {"S": f"TENANT#{tenant_id}"},
                "sk": {"S": f"MESSAGE#{message_id}"},
            },
        )

        item = response.get("Item")
        if not item:
            return None

        return self._item_to_message(item)

    @tracer.capture_method
    def list_messages(
        self,
        tenant_id: str,
        connection_id: str | None = None,
        limit: int = 50,
        start_date: datetime | None = None,
    ) -> list[EmailMessage]:
        """List email messages for a tenant."""
        key_condition = "pk = :pk"
        expr_values: dict[str, Any] = {":pk": {"S": f"TENANT#{tenant_id}"}}

        if connection_id:
            # Use GSI for connection-specific queries
            response = self.clients.dynamodb.query(
                TableName=self._messages_table,
                IndexName="connection-index",
                KeyConditionExpression="connection_id = :cid",
                ExpressionAttributeValues={":cid": {"S": connection_id}},
                Limit=limit,
                ScanIndexForward=False,  # Newest first
            )
        else:
            response = self.clients.dynamodb.query(
                TableName=self._messages_table,
                KeyConditionExpression=key_condition,
                ExpressionAttributeValues=expr_values,
                Limit=limit,
                ScanIndexForward=False,
            )

        return [self._item_to_message(item) for item in response.get("Items", [])]

    # =========================================================================
    # Email Processing Jobs
    # =========================================================================

    @tracer.capture_method
    def create_processing_job(
        self,
        tenant_id: str,
        connection_id: str,
        message_ids: list[str],
        job_type: str = "analysis",
    ) -> EmailProcessingJob:
        """Create an email processing job."""
        job = EmailProcessingJob(
            job_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            connection_id=connection_id,
            message_ids=message_ids,
            job_type=job_type,
            status="pending",
        )

        self.clients.dynamodb.put_item(
            TableName=self._jobs_table,
            Item={
                "pk": {"S": f"TENANT#{tenant_id}"},
                "sk": {"S": f"JOB#{job.job_id}"},
                "job_id": {"S": job.job_id},
                "connection_id": {"S": connection_id},
                "message_ids": {"SS": message_ids},
                "job_type": {"S": job_type},
                "status": {"S": "pending"},
                "created_at": {"S": job.created_at.isoformat()},
            },
        )

        # Queue the job for processing
        self._queue_job(job)

        return job

    def _queue_job(self, job: EmailProcessingJob) -> None:
        """Queue a job for async processing."""
        queue_url = f"https://sqs.{self.settings.aws_region}.amazonaws.com/{self.settings.project_name}-{self.settings.environment}-email-processing"

        self.clients.sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                "job_id": job.job_id,
                "tenant_id": job.tenant_id,
                "connection_id": job.connection_id,
                "message_ids": job.message_ids,
                "job_type": job.job_type,
            }),
            MessageGroupId=job.tenant_id,
            MessageDeduplicationId=job.job_id,
        )

    # =========================================================================
    # GenAI Email Analysis
    # =========================================================================

    @tracer.capture_method
    def analyze_email(
        self,
        message: EmailMessage,
        settings: TenantEmailSettings,
    ) -> EmailMessage:
        """Analyze an email using GenAI (Bedrock)."""
        analyses_to_run: list[AnalysisType] = []

        if settings.analyze_sentiment:
            analyses_to_run.append(AnalysisType.EMAIL_SENTIMENT)
        if settings.extract_action_items:
            analyses_to_run.append(AnalysisType.ACTION_EXTRACTION)
        if settings.priority_detection:
            analyses_to_run.append(AnalysisType.EMAIL_PRIORITY)

        # Build the prompt for analysis
        prompt = self._build_analysis_prompt(message, analyses_to_run)

        # Call Bedrock
        response = self._invoke_bedrock(prompt, message.tenant_id)

        # Parse and apply results
        if response:
            message = self._apply_analysis_results(message, response)
            message.processed_at = datetime.utcnow()

        return message

    def _build_analysis_prompt(
        self,
        message: EmailMessage,
        analyses: list[AnalysisType],
    ) -> str:
        """Build the GenAI prompt for email analysis."""
        analysis_instructions = []

        if AnalysisType.EMAIL_SENTIMENT in analyses:
            analysis_instructions.append(
                "- Sentiment: Classify as positive, negative, neutral, or mixed"
            )
        if AnalysisType.ACTION_EXTRACTION in analyses:
            analysis_instructions.append(
                "- Action Items: Extract any action items or tasks mentioned"
            )
        if AnalysisType.EMAIL_PRIORITY in analyses:
            analysis_instructions.append(
                "- Priority: Score from 0.0 (low) to 1.0 (urgent) based on content"
            )
        if AnalysisType.EMAIL_INTENT in analyses:
            analysis_instructions.append(
                "- Intent: Classify the primary intent (inquiry, request, complaint, "
                "information, follow-up, introduction, other)"
            )

        prompt = f"""Analyze the following email and provide structured analysis.

Email Subject: {message.subject}
From: {message.sender}
To: {', '.join(message.recipients)}
Received: {message.received_at.isoformat()}

Email Content:
{message.body_preview or '[No content preview available]'}

Provide the following analysis:
{chr(10).join(analysis_instructions)}

Respond in JSON format with the following structure:
{{
    "sentiment": "positive|negative|neutral|mixed",
    "intent": "inquiry|request|complaint|information|follow-up|introduction|other",
    "priority_score": 0.0-1.0,
    "action_items": ["action 1", "action 2"],
    "summary": "Brief 1-2 sentence summary",
    "entities": [{{"type": "person|company|date|amount", "value": "..."}}]
}}
"""
        return prompt

    def _invoke_bedrock(self, prompt: str, tenant_id: str) -> dict[str, Any] | None:
        """Invoke Bedrock for GenAI analysis."""
        try:
            response = self.clients.bedrock_runtime.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "temperature": 0.3,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                }),
            )

            response_body = json.loads(response["body"].read())
            content = response_body.get("content", [{}])[0].get("text", "")

            # Parse JSON from response
            # Try to extract JSON from the response
            if "{" in content and "}" in content:
                json_start = content.index("{")
                json_end = content.rindex("}") + 1
                json_str = content[json_start:json_end]
                return json.loads(json_str)

        except Exception as e:
            logger.exception(
                "Error invoking Bedrock",
                extra={"tenant_id": tenant_id, "error": str(e)},
            )

        return None

    def _apply_analysis_results(
        self,
        message: EmailMessage,
        results: dict[str, Any],
    ) -> EmailMessage:
        """Apply GenAI analysis results to the email message."""
        if "sentiment" in results:
            message.sentiment = results["sentiment"]
        if "intent" in results:
            message.intent = results["intent"]
        if "priority_score" in results:
            message.priority_score = float(results["priority_score"])
        if "action_items" in results:
            message.action_items = results["action_items"]
        if "summary" in results:
            message.summary = results["summary"]
        if "entities" in results:
            message.entities = results["entities"]

        return message

    # =========================================================================
    # Email Synchronization
    # =========================================================================

    @tracer.capture_method
    def sync_emails(
        self,
        tenant_id: str,
        connection_id: str,
        settings: TenantEmailSettings,
    ) -> int:
        """Sync emails from provider and process them."""
        connection = self.get_connection(tenant_id, connection_id)
        if not connection:
            logger.warning(
                "Connection not found",
                extra={"tenant_id": tenant_id, "connection_id": connection_id},
            )
            return 0

        if connection.status != EmailConnectionStatus.CONNECTED:
            logger.warning(
                "Connection not active",
                extra={"tenant_id": tenant_id, "status": connection.status.value},
            )
            return 0

        # Get emails from provider (mock implementation)
        # In real implementation, this would call Microsoft Graph or Google API
        emails = self._fetch_emails_from_provider(connection, settings)

        processed_count = 0
        for email_data in emails:
            message = self._create_message_from_provider_data(
                tenant_id, connection_id, email_data
            )

            # Analyze email if enabled
            if settings.enabled:
                message = self.analyze_email(message, settings)

            # Store the message
            self.store_message(message)
            processed_count += 1

        # Update last sync time
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

        logger.info(
            "Email sync completed",
            extra={
                "tenant_id": tenant_id,
                "connection_id": connection_id,
                "processed_count": processed_count,
            },
        )

        return processed_count

    def _fetch_emails_from_provider(
        self,
        connection: EmailConnection,
        settings: TenantEmailSettings,
    ) -> list[dict[str, Any]]:
        """Fetch emails from provider (mock implementation)."""
        # In real implementation, this would call:
        # - Microsoft Graph API for Microsoft 365
        # - Gmail API for Google Workspace

        # Mock data for demonstration
        return []

    def _create_message_from_provider_data(
        self,
        tenant_id: str,
        connection_id: str,
        data: dict[str, Any],
    ) -> EmailMessage:
        """Create EmailMessage from provider data."""
        return EmailMessage(
            message_id=data.get("id", str(uuid.uuid4())),
            tenant_id=tenant_id,
            connection_id=connection_id,
            subject=data.get("subject", ""),
            sender=data.get("from", ""),
            recipients=data.get("to", []),
            cc=data.get("cc", []),
            received_at=datetime.fromisoformat(
                data.get("receivedDateTime", datetime.utcnow().isoformat())
            ),
            body_preview=data.get("bodyPreview"),
            has_attachments=data.get("hasAttachments", False),
            is_read=data.get("isRead", False),
            importance=data.get("importance", "normal"),
            conversation_id=data.get("conversationId"),
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _connection_to_item(self, conn: EmailConnection) -> dict[str, Any]:
        """Convert EmailConnection to DynamoDB item."""
        return {
            "pk": {"S": f"TENANT#{conn.tenant_id}"},
            "sk": {"S": f"CONNECTION#{conn.connection_id}"},
            "connection_id": {"S": conn.connection_id},
            "tenant_id": {"S": conn.tenant_id},
            "provider": {"S": conn.provider.value},
            "status": {"S": conn.status.value},
            "email_address": {"S": conn.email_address},
            "display_name": {"S": conn.display_name or ""},
            "scopes": {"SS": conn.scopes} if conn.scopes else {"SS": ["default"]},
            "sync_enabled": {"BOOL": conn.sync_enabled},
            "created_at": {"S": conn.created_at.isoformat()},
            "updated_at": {"S": conn.updated_at.isoformat()},
            "metadata": {"S": json.dumps(conn.metadata)},
        }

    def _item_to_connection(self, item: dict[str, Any]) -> EmailConnection:
        """Convert DynamoDB item to EmailConnection."""
        return EmailConnection(
            connection_id=item["connection_id"]["S"],
            tenant_id=item["tenant_id"]["S"],
            provider=EmailProvider(item["provider"]["S"]),
            status=EmailConnectionStatus(item["status"]["S"]),
            email_address=item["email_address"]["S"],
            display_name=item.get("display_name", {}).get("S") or None,
            scopes=list(item.get("scopes", {}).get("SS", [])),
            sync_enabled=item.get("sync_enabled", {}).get("BOOL", True),
            created_at=datetime.fromisoformat(item["created_at"]["S"]),
            updated_at=datetime.fromisoformat(item["updated_at"]["S"]),
            metadata=json.loads(item.get("metadata", {}).get("S", "{}")),
        )

    def _message_to_item(self, msg: EmailMessage) -> dict[str, Any]:
        """Convert EmailMessage to DynamoDB item."""
        item = {
            "pk": {"S": f"TENANT#{msg.tenant_id}"},
            "sk": {"S": f"MESSAGE#{msg.message_id}"},
            "message_id": {"S": msg.message_id},
            "tenant_id": {"S": msg.tenant_id},
            "connection_id": {"S": msg.connection_id},
            "subject": {"S": msg.subject},
            "sender": {"S": msg.sender},
            "recipients": {"SS": msg.recipients} if msg.recipients else {"SS": ["none"]},
            "received_at": {"S": msg.received_at.isoformat()},
            "has_attachments": {"BOOL": msg.has_attachments},
            "is_read": {"BOOL": msg.is_read},
            "importance": {"S": msg.importance},
        }

        if msg.body_preview:
            item["body_preview"] = {"S": msg.body_preview}
        if msg.sentiment:
            item["sentiment"] = {"S": msg.sentiment}
        if msg.summary:
            item["summary"] = {"S": msg.summary}
        if msg.intent:
            item["intent"] = {"S": msg.intent}
        if msg.priority_score is not None:
            item["priority_score"] = {"N": str(msg.priority_score)}
        if msg.action_items:
            item["action_items"] = {"SS": msg.action_items}
        if msg.processed_at:
            item["processed_at"] = {"S": msg.processed_at.isoformat()}

        return item

    def _item_to_message(self, item: dict[str, Any]) -> EmailMessage:
        """Convert DynamoDB item to EmailMessage."""
        return EmailMessage(
            message_id=item["message_id"]["S"],
            tenant_id=item["tenant_id"]["S"],
            connection_id=item["connection_id"]["S"],
            subject=item["subject"]["S"],
            sender=item["sender"]["S"],
            recipients=list(item.get("recipients", {}).get("SS", [])),
            received_at=datetime.fromisoformat(item["received_at"]["S"]),
            body_preview=item.get("body_preview", {}).get("S"),
            has_attachments=item.get("has_attachments", {}).get("BOOL", False),
            is_read=item.get("is_read", {}).get("BOOL", False),
            importance=item.get("importance", {}).get("S", "normal"),
            sentiment=item.get("sentiment", {}).get("S"),
            summary=item.get("summary", {}).get("S"),
            intent=item.get("intent", {}).get("S"),
            priority_score=float(item["priority_score"]["N"])
            if "priority_score" in item
            else None,
            action_items=list(item.get("action_items", {}).get("SS", [])),
            processed_at=datetime.fromisoformat(item["processed_at"]["S"])
            if "processed_at" in item
            else None,
        )
