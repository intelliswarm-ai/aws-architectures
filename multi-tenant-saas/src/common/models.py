"""Pydantic models for the enterprise serverless platform."""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Generic Types
# =============================================================================

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    data: T | None = None
    error: str | None = None
    message: str | None = None
    request_id: str | None = Field(None, alias="requestId")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[T]
    total: int
    page: int = 1
    page_size: int = Field(20, alias="pageSize")
    has_next: bool = Field(False, alias="hasNext")
    has_previous: bool = Field(False, alias="hasPrevious")


# =============================================================================
# Tenant Models
# =============================================================================


class TenantStatus(str, Enum):
    """Tenant account status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class TenantTier(str, Enum):
    """Tenant subscription tier."""

    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantInfo(BaseModel):
    """Tenant information from Cognito claims or database."""

    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(..., alias="tenantId")
    name: str
    status: TenantStatus = TenantStatus.ACTIVE
    tier: TenantTier = TenantTier.FREE
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    settings: dict[str, Any] = Field(default_factory=dict)


class TenantContext(BaseModel):
    """Current tenant context for request processing."""

    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(..., alias="tenantId")
    user_id: str = Field(..., alias="userId")
    email: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    tier: TenantTier = TenantTier.FREE
    metadata: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Audit Models
# =============================================================================


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"

    # Authorization
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"

    # Data operations
    DATA_CREATE = "data_create"
    DATA_READ = "data_read"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"

    # Admin operations
    CONFIG_CHANGE = "config_change"
    SECRET_ACCESS = "secret_access"
    SECRET_ROTATION = "secret_rotation"

    # Security events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"


class AuditEvent(BaseModel):
    """Audit event record."""

    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(..., alias="eventId")
    event_type: AuditEventType = Field(..., alias="eventType")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: str | None = Field(None, alias="tenantId")
    user_id: str | None = Field(None, alias="userId")
    source_ip: str | None = Field(None, alias="sourceIp")
    user_agent: str | None = Field(None, alias="userAgent")
    resource: str | None = None
    action: str | None = None
    result: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = Field(None, alias="requestId")


# =============================================================================
# API Gateway Models
# =============================================================================


class AuthorizerPolicy(BaseModel):
    """IAM policy for API Gateway authorizer response."""

    model_config = ConfigDict(populate_by_name=True)

    principal_id: str = Field(..., alias="principalId")
    policy_document: dict[str, Any] = Field(..., alias="policyDocument")
    context: dict[str, Any] = Field(default_factory=dict)


class ApiGatewayEvent(BaseModel):
    """Parsed API Gateway event."""

    model_config = ConfigDict(populate_by_name=True)

    http_method: str = Field(..., alias="httpMethod")
    path: str
    path_parameters: dict[str, str] | None = Field(None, alias="pathParameters")
    query_parameters: dict[str, str] | None = Field(None, alias="queryStringParameters")
    headers: dict[str, str] = Field(default_factory=dict)
    body: str | None = None
    is_base64_encoded: bool = Field(False, alias="isBase64Encoded")
    request_context: dict[str, Any] = Field(default_factory=dict, alias="requestContext")


# =============================================================================
# EventBridge Models
# =============================================================================


class EventBridgeEvent(BaseModel):
    """EventBridge event structure."""

    model_config = ConfigDict(populate_by_name=True)

    version: str = "0"
    id: str
    detail_type: str = Field(..., alias="detail-type")
    source: str
    account: str
    time: datetime
    region: str
    resources: list[str] = Field(default_factory=list)
    detail: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# SQS Models
# =============================================================================


class SqsMessage(BaseModel):
    """SQS message structure."""

    model_config = ConfigDict(populate_by_name=True)

    message_id: str = Field(..., alias="messageId")
    receipt_handle: str = Field(..., alias="receiptHandle")
    body: str
    attributes: dict[str, str] = Field(default_factory=dict)
    message_attributes: dict[str, Any] = Field(default_factory=dict, alias="messageAttributes")
    md5_of_body: str = Field(..., alias="md5OfBody")
    event_source: str = Field("aws:sqs", alias="eventSource")
    event_source_arn: str = Field(..., alias="eventSourceARN")
    aws_region: str = Field(..., alias="awsRegion")


class SqsBatchItemFailure(BaseModel):
    """SQS batch item failure for partial batch response."""

    model_config = ConfigDict(populate_by_name=True)

    item_identifier: str = Field(..., alias="itemIdentifier")


class SqsBatchResponse(BaseModel):
    """SQS batch processing response."""

    model_config = ConfigDict(populate_by_name=True)

    batch_item_failures: list[SqsBatchItemFailure] = Field(
        default_factory=list, alias="batchItemFailures"
    )


# =============================================================================
# Secrets Manager Models
# =============================================================================


class RotationStep(str, Enum):
    """Secrets Manager rotation steps."""

    CREATE_SECRET = "createSecret"
    SET_SECRET = "setSecret"
    TEST_SECRET = "testSecret"
    FINISH_SECRET = "finishSecret"


class SecretRotationEvent(BaseModel):
    """Secrets Manager rotation Lambda event."""

    model_config = ConfigDict(populate_by_name=True)

    step: RotationStep = Field(..., alias="Step")
    secret_id: str = Field(..., alias="SecretId")
    client_request_token: str = Field(..., alias="ClientRequestToken")


# =============================================================================
# Email Integration Models (Microsoft Graph, Google Workspace)
# =============================================================================


class EmailProvider(str, Enum):
    """Supported email providers."""

    MICROSOFT_365 = "microsoft_365"
    GOOGLE_WORKSPACE = "google_workspace"
    CUSTOM_IMAP = "custom_imap"


class EmailConnectionStatus(str, Enum):
    """Email connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING = "pending"
    ERROR = "error"
    EXPIRED = "expired"


class EmailConnection(BaseModel):
    """Tenant email connection configuration."""

    model_config = ConfigDict(populate_by_name=True)

    connection_id: str = Field(..., alias="connectionId")
    tenant_id: str = Field(..., alias="tenantId")
    provider: EmailProvider
    status: EmailConnectionStatus = EmailConnectionStatus.PENDING
    email_address: str = Field(..., alias="emailAddress")
    display_name: str | None = Field(None, alias="displayName")
    scopes: list[str] = Field(default_factory=list)
    token_expires_at: datetime | None = Field(None, alias="tokenExpiresAt")
    last_sync_at: datetime | None = Field(None, alias="lastSyncAt")
    sync_enabled: bool = Field(True, alias="syncEnabled")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmailMessage(BaseModel):
    """Processed email message."""

    model_config = ConfigDict(populate_by_name=True)

    message_id: str = Field(..., alias="messageId")
    tenant_id: str = Field(..., alias="tenantId")
    connection_id: str = Field(..., alias="connectionId")
    subject: str
    sender: str
    recipients: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    received_at: datetime = Field(..., alias="receivedAt")
    body_preview: str | None = Field(None, alias="bodyPreview")
    has_attachments: bool = Field(False, alias="hasAttachments")
    is_read: bool = Field(False, alias="isRead")
    importance: str = "normal"
    categories: list[str] = Field(default_factory=list)
    conversation_id: str | None = Field(None, alias="conversationId")
    # GenAI analysis results
    sentiment: str | None = None
    summary: str | None = None
    intent: str | None = None
    entities: list[dict[str, Any]] = Field(default_factory=list)
    priority_score: float | None = Field(None, alias="priorityScore")
    action_items: list[str] = Field(default_factory=list, alias="actionItems")
    processed_at: datetime | None = Field(None, alias="processedAt")


class EmailProcessingJob(BaseModel):
    """Email processing job for GenAI analysis."""

    model_config = ConfigDict(populate_by_name=True)

    job_id: str = Field(..., alias="jobId")
    tenant_id: str = Field(..., alias="tenantId")
    connection_id: str = Field(..., alias="connectionId")
    message_ids: list[str] = Field(..., alias="messageIds")
    job_type: str = Field("analysis", alias="jobType")
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    started_at: datetime | None = Field(None, alias="startedAt")
    completed_at: datetime | None = Field(None, alias="completedAt")
    error: str | None = None
    results: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# CRM Integration Models (Salesforce, HubSpot, etc.)
# =============================================================================


class CRMProvider(str, Enum):
    """Supported CRM providers."""

    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    DYNAMICS_365 = "dynamics_365"
    PIPEDRIVE = "pipedrive"
    ZOHO = "zoho"
    CUSTOM = "custom"


class CRMConnectionStatus(str, Enum):
    """CRM connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING = "pending"
    ERROR = "error"
    EXPIRED = "expired"


class CRMConnection(BaseModel):
    """Tenant CRM connection configuration."""

    model_config = ConfigDict(populate_by_name=True)

    connection_id: str = Field(..., alias="connectionId")
    tenant_id: str = Field(..., alias="tenantId")
    provider: CRMProvider
    status: CRMConnectionStatus = CRMConnectionStatus.PENDING
    instance_url: str | None = Field(None, alias="instanceUrl")
    organization_id: str | None = Field(None, alias="organizationId")
    user_id: str | None = Field(None, alias="userId")
    scopes: list[str] = Field(default_factory=list)
    token_expires_at: datetime | None = Field(None, alias="tokenExpiresAt")
    last_sync_at: datetime | None = Field(None, alias="lastSyncAt")
    sync_enabled: bool = Field(True, alias="syncEnabled")
    sync_direction: str = "bidirectional"  # inbound, outbound, bidirectional
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    metadata: dict[str, Any] = Field(default_factory=dict)


class CRMContact(BaseModel):
    """CRM contact record."""

    model_config = ConfigDict(populate_by_name=True)

    contact_id: str = Field(..., alias="contactId")
    tenant_id: str = Field(..., alias="tenantId")
    connection_id: str = Field(..., alias="connectionId")
    external_id: str = Field(..., alias="externalId")  # ID in the CRM system
    email: str
    first_name: str | None = Field(None, alias="firstName")
    last_name: str | None = Field(None, alias="lastName")
    company: str | None = None
    title: str | None = None
    phone: str | None = None
    last_activity_at: datetime | None = Field(None, alias="lastActivityAt")
    lead_score: float | None = Field(None, alias="leadScore")
    lifecycle_stage: str | None = Field(None, alias="lifecycleStage")
    owner_id: str | None = Field(None, alias="ownerId")
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict, alias="customFields")
    synced_at: datetime = Field(default_factory=datetime.utcnow, alias="syncedAt")


class CRMDeal(BaseModel):
    """CRM deal/opportunity record."""

    model_config = ConfigDict(populate_by_name=True)

    deal_id: str = Field(..., alias="dealId")
    tenant_id: str = Field(..., alias="tenantId")
    connection_id: str = Field(..., alias="connectionId")
    external_id: str = Field(..., alias="externalId")
    name: str
    amount: float | None = None
    currency: str = "USD"
    stage: str
    probability: float | None = None
    close_date: datetime | None = Field(None, alias="closeDate")
    contact_ids: list[str] = Field(default_factory=list, alias="contactIds")
    owner_id: str | None = Field(None, alias="ownerId")
    pipeline_id: str | None = Field(None, alias="pipelineId")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    custom_fields: dict[str, Any] = Field(default_factory=dict, alias="customFields")
    synced_at: datetime = Field(default_factory=datetime.utcnow, alias="syncedAt")


class CRMActivity(BaseModel):
    """CRM activity record (calls, meetings, tasks)."""

    model_config = ConfigDict(populate_by_name=True)

    activity_id: str = Field(..., alias="activityId")
    tenant_id: str = Field(..., alias="tenantId")
    connection_id: str = Field(..., alias="connectionId")
    external_id: str = Field(..., alias="externalId")
    activity_type: str = Field(..., alias="activityType")  # call, meeting, task, email
    subject: str
    description: str | None = None
    contact_ids: list[str] = Field(default_factory=list, alias="contactIds")
    deal_ids: list[str] = Field(default_factory=list, alias="dealIds")
    owner_id: str | None = Field(None, alias="ownerId")
    due_date: datetime | None = Field(None, alias="dueDate")
    completed_at: datetime | None = Field(None, alias="completedAt")
    status: str = "pending"
    outcome: str | None = None
    duration_minutes: int | None = Field(None, alias="durationMinutes")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    synced_at: datetime = Field(default_factory=datetime.utcnow, alias="syncedAt")


# =============================================================================
# GenAI Analysis Models
# =============================================================================


class AnalysisType(str, Enum):
    """Types of GenAI analysis."""

    EMAIL_SENTIMENT = "email_sentiment"
    EMAIL_SUMMARY = "email_summary"
    EMAIL_INTENT = "email_intent"
    EMAIL_PRIORITY = "email_priority"
    CONTACT_ENRICHMENT = "contact_enrichment"
    DEAL_INTELLIGENCE = "deal_intelligence"
    CONVERSATION_ANALYSIS = "conversation_analysis"
    ACTION_EXTRACTION = "action_extraction"


class GenAIAnalysisRequest(BaseModel):
    """Request for GenAI analysis."""

    model_config = ConfigDict(populate_by_name=True)

    request_id: str = Field(..., alias="requestId")
    tenant_id: str = Field(..., alias="tenantId")
    analysis_type: AnalysisType = Field(..., alias="analysisType")
    input_data: dict[str, Any] = Field(..., alias="inputData")
    model_id: str = Field("anthropic.claude-3-sonnet-20240229-v1:0", alias="modelId")
    parameters: dict[str, Any] = Field(default_factory=dict)
    callback_url: str | None = Field(None, alias="callbackUrl")


class GenAIAnalysisResult(BaseModel):
    """Result from GenAI analysis."""

    model_config = ConfigDict(populate_by_name=True)

    result_id: str = Field(..., alias="resultId")
    request_id: str = Field(..., alias="requestId")
    tenant_id: str = Field(..., alias="tenantId")
    analysis_type: AnalysisType = Field(..., alias="analysisType")
    status: str = "completed"
    output: dict[str, Any] = Field(default_factory=dict)
    tokens_used: int = Field(0, alias="tokensUsed")
    latency_ms: int = Field(0, alias="latencyMs")
    model_id: str = Field(..., alias="modelId")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    error: str | None = None


# =============================================================================
# Tenant Configuration Models
# =============================================================================


class TenantEmailSettings(BaseModel):
    """Tenant email processing settings."""

    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = True
    auto_sync: bool = Field(True, alias="autoSync")
    sync_interval_minutes: int = Field(15, alias="syncIntervalMinutes")
    process_incoming: bool = Field(True, alias="processIncoming")
    process_outgoing: bool = Field(False, alias="processOutgoing")
    analyze_sentiment: bool = Field(True, alias="analyzeSentiment")
    extract_action_items: bool = Field(True, alias="extractActionItems")
    summarize_threads: bool = Field(True, alias="summarizeThreads")
    priority_detection: bool = Field(True, alias="priorityDetection")
    max_emails_per_sync: int = Field(100, alias="maxEmailsPerSync")
    retention_days: int = Field(90, alias="retentionDays")


class TenantCRMSettings(BaseModel):
    """Tenant CRM integration settings."""

    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = True
    auto_sync: bool = Field(True, alias="autoSync")
    sync_interval_minutes: int = Field(30, alias="syncIntervalMinutes")
    sync_contacts: bool = Field(True, alias="syncContacts")
    sync_deals: bool = Field(True, alias="syncDeals")
    sync_activities: bool = Field(True, alias="syncActivities")
    enrich_contacts: bool = Field(True, alias="enrichContacts")
    create_activities_from_emails: bool = Field(True, alias="createActivitiesFromEmails")
    update_contact_scores: bool = Field(True, alias="updateContactScores")


class TenantGenAISettings(BaseModel):
    """Tenant GenAI settings."""

    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = True
    model_id: str = Field("anthropic.claude-3-sonnet-20240229-v1:0", alias="modelId")
    max_tokens_per_request: int = Field(4096, alias="maxTokensPerRequest")
    daily_token_limit: int = Field(100000, alias="dailyTokenLimit")
    temperature: float = 0.3
    enable_caching: bool = Field(True, alias="enableCaching")


class TenantConfiguration(BaseModel):
    """Complete tenant configuration."""

    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str = Field(..., alias="tenantId")
    email_settings: TenantEmailSettings = Field(
        default_factory=TenantEmailSettings, alias="emailSettings"
    )
    crm_settings: TenantCRMSettings = Field(
        default_factory=TenantCRMSettings, alias="crmSettings"
    )
    genai_settings: TenantGenAISettings = Field(
        default_factory=TenantGenAISettings, alias="genaiSettings"
    )
    webhooks: dict[str, str] = Field(default_factory=dict)
    custom_settings: dict[str, Any] = Field(default_factory=dict, alias="customSettings")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
