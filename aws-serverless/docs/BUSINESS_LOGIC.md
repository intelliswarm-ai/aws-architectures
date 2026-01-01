# Enterprise Serverless Platform - Business Logic Documentation

This document describes the business logic, data flows, and processing rules for the Multi-Tenant Enterprise Serverless Platform (intelliswarm.ai).

## Table of Contents

1. [System Overview](#system-overview)
2. [Multi-Tenancy Architecture](#multi-tenancy-architecture)
3. [Authentication and Authorization](#authentication-and-authorization)
4. [Email Intelligence Pipeline](#email-intelligence-pipeline)
5. [CRM Integration Logic](#crm-integration-logic)
6. [GenAI Analysis Engine](#genai-analysis-engine)
7. [Audit and Compliance](#audit-and-compliance)
8. [Subscription Tiers and Limits](#subscription-tiers-and-limits)

---

## System Overview

### Purpose

The Enterprise Serverless Platform is a multi-tenant SaaS solution providing:
- **Email Intelligence**: Connect Microsoft 365/Google Workspace and analyze emails with GenAI
- **CRM Integration**: Sync contacts, deals, and activities with Salesforce, HubSpot, Dynamics 365
- **Smart Prioritization**: AI-powered sentiment analysis, intent detection, and priority scoring
- **Action Extraction**: Automatically extract action items and tasks from conversations

### Target Market

- Enterprise organizations with 50-10,000 employees
- Sales and customer success teams
- Email-heavy industries (consulting, legal, finance)

---

## Multi-Tenancy Architecture

### Tenant Isolation Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TENANT ISOLATION LAYERS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Layer 1: API Gateway + WAF                                              ││
│  │ - Rate limiting per API key                                             ││
│  │ - Request validation                                                    ││
│  │ - IP allowlisting (enterprise tier)                                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Layer 2: Lambda Authorizer                                              ││
│  │ - JWT validation                                                        ││
│  │ - Tenant ID extraction                                                  ││
│  │ - Permission boundary enforcement                                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Layer 3: Service Layer                                                  ││
│  │ - Tenant context injection                                              ││
│  │ - Cross-tenant access prevention                                        ││
│  │ - Tier-based feature gating                                             ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Layer 4: Data Layer (DynamoDB)                                          ││
│  │ - Partition key: TENANT#{tenant_id}                                     ││
│  │ - All queries scoped to tenant                                          ││
│  │ - No cross-tenant data leakage possible                                 ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tenant Context Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    REQUEST CONTEXT FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HTTP Request                                                   │
│  Authorization: Bearer {JWT}                                    │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────┐                                            │
│  │ Lambda          │                                            │
│  │ Authorizer      │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ JWT Payload Extraction:                                     ││
│  │                                                             ││
│  │ {                                                           ││
│  │   "sub": "user-123",                                        ││
│  │   "tenant_id": "tenant-456",                                ││
│  │   "email": "user@company.com",                              ││
│  │   "roles": ["admin", "user"],                               ││
│  │   "tier": "professional"                                    ││
│  │ }                                                           ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ TenantContext Object:                                       ││
│  │                                                             ││
│  │ class TenantContext:                                        ││
│  │     tenant_id: str                                          ││
│  │     user_id: str                                            ││
│  │     email: str                                              ││
│  │     roles: list[str]                                        ││
│  │     permissions: list[str]                                  ││
│  │     tier: TenantTier                                        ││
│  │     metadata: dict                                          ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ API Handler     │ (context passed to all services)           │
│  │ with context    │                                            │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Authentication and Authorization

### JWT Token Structure

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "cognito-key-id"
  },
  "payload": {
    "sub": "user-uuid",
    "iss": "https://cognito-idp.region.amazonaws.com/pool-id",
    "aud": "client-id",
    "exp": 1704931200,
    "iat": 1704927600,
    "tenant_id": "tenant-uuid",
    "email": "user@company.com",
    "roles": ["admin"],
    "tier": "professional",
    "custom:company": "Acme Corp"
  }
}
```

### Permission Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERMISSION HIERARCHY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Tier Permissions (cumulative):                                 │
│                                                                 │
│  FREE        → email:read (1 connection limit)                  │
│       │                                                         │
│       ▼                                                         │
│  BASIC       → + email:write + crm:read (1 each)                │
│       │                                                         │
│       ▼                                                         │
│  PROFESSIONAL → + crm:write + activity:create (unlimited)       │
│       │                                                         │
│       ▼                                                         │
│  ENTERPRISE  → + admin:* + audit:read + custom features         │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Role Permissions:                                              │
│                                                                 │
│  owner  → All permissions for tenant                            │
│  admin  → All except billing                                    │
│  user   → Read + limited write                                  │
│  viewer → Read only                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Authorization Check Flow

```python
def check_permission(context: TenantContext, resource: str, action: str) -> bool:
    # 1. Check if tier allows this feature
    if not tier_allows(context.tier, resource):
        return False

    # 2. Check if role has permission
    required_permission = f"{resource}:{action}"
    if required_permission not in context.permissions:
        return False

    # 3. Check resource limits
    if exceeds_tier_limits(context.tenant_id, resource):
        return False

    return True
```

---

## Email Intelligence Pipeline

### Email Connection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   EMAIL CONNECTION FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User initiates connection                                      │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────┐                                            │
│  │ Select provider │                                            │
│  │ - Microsoft 365 │                                            │
│  │ - Google        │                                            │
│  │ - IMAP          │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ OAuth 2.0 Flow (Microsoft/Google)                           ││
│  │                                                             ││
│  │ 1. Redirect to provider login                               ││
│  │ 2. User grants permissions                                  ││
│  │ 3. Receive authorization code                               ││
│  │ 4. Exchange for access + refresh tokens                     ││
│  │ 5. Store tokens in Secrets Manager                          ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Create          │                                            │
│  │ EmailConnection │                                            │
│  │ record in       │                                            │
│  │ DynamoDB        │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Queue initial   │                                            │
│  │ sync job        │                                            │
│  │ (SQS)           │                                            │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Email Sync and Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                EMAIL PROCESSING PIPELINE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐                                            │
│  │ Scheduled       │ (every 15 minutes per connection)          │
│  │ EventBridge     │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Fetch new       │                                            │
│  │ emails from     │                                            │
│  │ provider API    │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ For each email:                                             ││
│  │                                                             ││
│  │ 1. Store raw email in DynamoDB                              ││
│  │ 2. Queue for GenAI analysis (SQS)                           ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ GenAI Analysis (Amazon Bedrock - Claude 3 Sonnet)           ││
│  │                                                             ││
│  │ Prompt:                                                     ││
│  │ "Analyze this email and extract:                            ││
│  │  - Sentiment (positive/negative/neutral)                    ││
│  │  - Intent (inquiry/complaint/request/information)           ││
│  │  - Priority score (1-10)                                    ││
│  │  - Action items (list of tasks)                             ││
│  │  - Key entities (people, companies, dates)                  ││
│  │  - Summary (2-3 sentences)"                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Update email    │                                            │
│  │ record with     │                                            │
│  │ analysis        │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Create CRM      │ (if CRM connected)                         │
│  │ activity        │                                            │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Email Analysis Result Model

```json
{
  "message_id": "msg-uuid",
  "tenant_id": "tenant-uuid",
  "connection_id": "conn-uuid",
  "subject": "Re: Q4 Contract Renewal",
  "from_address": "client@company.com",
  "to_addresses": ["sales@ourcompany.com"],
  "received_at": "2024-01-15T10:30:00Z",
  "analysis": {
    "sentiment": "positive",
    "sentiment_score": 0.85,
    "intent": "request",
    "priority_score": 8,
    "action_items": [
      "Schedule call for contract discussion",
      "Send updated pricing proposal"
    ],
    "entities": {
      "people": ["John Smith", "Sarah Johnson"],
      "companies": ["Acme Corp"],
      "dates": ["2024-01-20", "Q4 2024"],
      "amounts": ["$50,000"]
    },
    "summary": "Client expressing interest in renewing contract with expanded scope. Requesting meeting to discuss terms and pricing for Q4.",
    "tokens_used": 1250,
    "model_id": "anthropic.claude-3-sonnet"
  }
}
```

---

## CRM Integration Logic

### Supported CRM Providers

| Provider | API Type | Features |
|----------|----------|----------|
| Salesforce | REST | Contacts, Accounts, Opportunities, Activities |
| HubSpot | REST | Contacts, Companies, Deals, Tasks |
| Dynamics 365 | OData | Contacts, Accounts, Opportunities, Activities |
| Pipedrive | REST | Persons, Organizations, Deals, Activities |
| Zoho CRM | REST | Contacts, Accounts, Deals, Tasks |

### CRM Sync Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      CRM SYNC FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐                                            │
│  │ Sync Direction  │                                            │
│  │ Configuration   │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│     ┌─────┴─────────────────┐                                   │
│     │                       │                                   │
│     ▼                       ▼                                   │
│  INBOUND              BIDIRECTIONAL                             │
│  (CRM → Platform)     (Both ways)                               │
│     │                       │                                   │
│     ▼                       ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Scheduled Sync (every 30 minutes)                           ││
│  │                                                             ││
│  │ 1. Fetch updated records from CRM (delta sync)              ││
│  │    - Use modified_since filter                              ││
│  │    - Paginate through results                               ││
│  │                                                             ││
│  │ 2. Transform to internal format                             ││
│  │    - Map CRM fields to standard schema                      ││
│  │    - Handle custom fields                                   ││
│  │                                                             ││
│  │ 3. Upsert to DynamoDB                                       ││
│  │    - Use external_id for matching                           ││
│  │    - Track sync_timestamp                                   ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Activity Creation (from analyzed emails)                    ││
│  │                                                             ││
│  │ When email analyzed with priority_score >= 7:               ││
│  │                                                             ││
│  │ 1. Find matching CRM contact by email address               ││
│  │ 2. Create activity record:                                  ││
│  │    - Type: EMAIL                                            ││
│  │    - Subject: Email subject                                 ││
│  │    - Description: GenAI summary                             ││
│  │    - Due date: If action items have dates                   ││
│  │ 3. Push to CRM via API (if bidirectional)                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Contact Matching Algorithm

```python
def find_crm_contact(email_address: str, tenant_id: str) -> CRMContact | None:
    # 1. Exact email match
    contact = query_by_email(tenant_id, email_address)
    if contact:
        return contact

    # 2. Domain match for company association
    domain = extract_domain(email_address)
    company = query_company_by_domain(tenant_id, domain)
    if company:
        # Return primary contact for company
        return query_primary_contact(tenant_id, company.id)

    # 3. Create new contact if auto-create enabled
    if tenant_settings.auto_create_contacts:
        return create_contact_from_email(tenant_id, email_address)

    return None
```

---

## GenAI Analysis Engine

### Bedrock Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                   GENAI ANALYSIS ENGINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Model Configuration                                         ││
│  │                                                             ││
│  │ Provider: Amazon Bedrock                                    ││
│  │ Model: anthropic.claude-3-sonnet-20240229-v1:0              ││
│  │ Max Tokens: 4096                                            ││
│  │ Temperature: 0.3 (low for consistency)                      ││
│  │ Top P: 0.9                                                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Analysis Types                                              ││
│  │                                                             ││
│  │ EMAIL_ANALYSIS:                                             ││
│  │   - Sentiment detection                                     ││
│  │   - Intent classification                                   ││
│  │   - Priority scoring                                        ││
│  │   - Entity extraction                                       ││
│  │   - Action item extraction                                  ││
│  │   - Summarization                                           ││
│  │                                                             ││
│  │ CONVERSATION_THREAD:                                        ││
│  │   - Thread summary                                          ││
│  │   - Key decisions                                           ││
│  │   - Open questions                                          ││
│  │   - Relationship health score                               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Rate Limiting                                               ││
│  │                                                             ││
│  │ Tier Limits (requests per minute):                          ││
│  │   FREE: 10 RPM                                              ││
│  │   BASIC: 50 RPM                                             ││
│  │   PROFESSIONAL: 200 RPM                                     ││
│  │   ENTERPRISE: 1000 RPM                                      ││
│  │                                                             ││
│  │ Token Limits (per month):                                   ││
│  │   FREE: 100K tokens                                         ││
│  │   BASIC: 1M tokens                                          ││
│  │   PROFESSIONAL: 10M tokens                                  ││
│  │   ENTERPRISE: Unlimited                                     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Analysis Prompt Template

```
You are an AI assistant analyzing business emails. Analyze the following email and provide a structured response.

EMAIL:
From: {from_address}
To: {to_addresses}
Subject: {subject}
Date: {received_at}

{body}

---

Provide your analysis in the following JSON format:
{
  "sentiment": "positive" | "negative" | "neutral" | "mixed",
  "sentiment_score": 0.0 to 1.0,
  "intent": "inquiry" | "complaint" | "request" | "information" | "negotiation" | "follow_up",
  "priority_score": 1 to 10,
  "action_items": ["list of specific action items"],
  "entities": {
    "people": ["names mentioned"],
    "companies": ["company names"],
    "dates": ["dates/deadlines"],
    "amounts": ["monetary values"]
  },
  "summary": "2-3 sentence summary of the email content and context"
}
```

---

## Audit and Compliance

### Audit Event Types

| Event Type | Description | Retention |
|------------|-------------|-----------|
| `LOGIN` | User authentication events | 90 days |
| `ACCESS_CONTROL` | Permission checks, denials | 90 days |
| `DATA_OPERATION` | CRUD on tenant data | 90 days |
| `CONFIG_CHANGE` | Settings modifications | 1 year |
| `SECURITY_EVENT` | Suspicious activity | 1 year |
| `INTEGRATION` | External API calls | 30 days |

### Audit Record Structure

```json
{
  "event_id": "evt-uuid",
  "tenant_id": "tenant-uuid",
  "user_id": "user-uuid",
  "event_type": "DATA_OPERATION",
  "timestamp": "2024-01-15T10:30:00Z",
  "resource_type": "email_connection",
  "resource_id": "conn-uuid",
  "action": "create",
  "result": "success",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "request_id": "req-uuid",
  "changes": {
    "before": null,
    "after": {"provider": "microsoft365", "status": "active"}
  },
  "ttl": 1712188800
}
```

### Audit Query Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                     AUDIT QUERY PATTERNS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DynamoDB Table: audits                                         │
│  PK: TENANT#{tenant_id}                                         │
│  SK: EVENT#{timestamp}                                          │
│                                                                 │
│  GSI: event-type-index                                          │
│  PK: EVENT_TYPE#{event_type}                                    │
│  SK: {timestamp}                                                │
│                                                                 │
│  Query Examples:                                                │
│                                                                 │
│  1. All events for tenant in date range:                        │
│     PK = TENANT#abc123                                          │
│     SK BETWEEN EVENT#2024-01-01 AND EVENT#2024-01-31            │
│                                                                 │
│  2. All login failures:                                         │
│     GSI: EVENT_TYPE#LOGIN                                       │
│     Filter: result = "failure"                                  │
│                                                                 │
│  3. User activity trail:                                        │
│     PK = TENANT#abc123                                          │
│     Filter: user_id = "user-xyz"                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Subscription Tiers and Limits

### Tier Comparison

| Feature | FREE | BASIC | PROFESSIONAL | ENTERPRISE |
|---------|------|-------|--------------|------------|
| Email Connections | 1 | 1 | Unlimited | Unlimited |
| CRM Connections | 0 | 1 | Unlimited | Unlimited |
| Users | 1 | 5 | 25 | Unlimited |
| Email Analysis/mo | 100 | 1,000 | 10,000 | Unlimited |
| GenAI Tokens/mo | 100K | 1M | 10M | Unlimited |
| Activity Creation | No | No | Yes | Yes |
| Custom Integrations | No | No | No | Yes |
| SSO/SAML | No | No | No | Yes |
| Audit Log Retention | 7 days | 30 days | 90 days | 1 year |
| Support | Community | Email | Priority | Dedicated |

### Limit Enforcement

```python
def check_tier_limits(tenant_id: str, resource: str) -> bool:
    tenant = get_tenant(tenant_id)
    limits = TIER_LIMITS[tenant.tier]

    current_count = count_resources(tenant_id, resource)
    max_allowed = limits.get(resource, 0)

    if max_allowed == -1:  # Unlimited
        return True

    return current_count < max_allowed

# Usage tracking
def track_usage(tenant_id: str, metric: str, amount: int = 1):
    key = f"{tenant_id}:{metric}:{current_month()}"
    increment_counter(key, amount)

    # Check if approaching limit
    current = get_counter(key)
    limit = get_limit(tenant_id, metric)

    if current >= limit * 0.8:
        send_warning_notification(tenant_id, metric, current, limit)
```

---

## Appendix: DynamoDB Table Schemas

### Tenants Table

```
PK: TENANT#{tenant_id}
SK: METADATA

Attributes:
- tenant_id, name, tier, status
- created_at, updated_at
- settings (JSON)
- billing_email
- owner_user_id
```

### Email Connections Table

```
PK: TENANT#{tenant_id}
SK: CONNECTION#{connection_id}

Attributes:
- connection_id, provider, email_address
- status (active/inactive/error)
- auth_status, token_expiry
- last_sync_at, sync_errors
- settings (JSON)
```

### Email Messages Table

```
PK: TENANT#{tenant_id}
SK: MESSAGE#{message_id}

GSI: connection-index
PK: CONNECTION#{connection_id}
SK: {received_at}

Attributes:
- message_id, connection_id
- subject, from_address, to_addresses
- received_at, processed_at
- analysis (JSON)
- crm_activity_id (if created)
```

### CRM Connections Table

```
PK: TENANT#{tenant_id}
SK: CRM#{connection_id}

Attributes:
- connection_id, provider, instance_url
- sync_direction (inbound/bidirectional)
- auth_status, last_sync_at
- object_mappings (JSON)
```

### CRM Contacts Table

```
PK: TENANT#{tenant_id}
SK: CONTACT#{contact_id}

GSI: email-index
PK: EMAIL#{email_address}
SK: TENANT#{tenant_id}

Attributes:
- contact_id, external_id, crm_connection_id
- first_name, last_name, email
- company_id, job_title
- lead_score, lifecycle_stage
- custom_fields (JSON)
- synced_at
```

---

## Appendix: Environment Variables

| Variable | Description |
|----------|-------------|
| `COGNITO_USER_POOL_ID` | Cognito user pool for auth |
| `COGNITO_CLIENT_ID` | Cognito app client ID |
| `TENANTS_TABLE` | DynamoDB tenants table |
| `EMAILS_TABLE` | DynamoDB emails table |
| `CRM_TABLE` | DynamoDB CRM data table |
| `AUDIT_TABLE` | DynamoDB audit table |
| `BEDROCK_MODEL_ID` | Claude model ID |
| `SECRETS_PREFIX` | Secrets Manager prefix |
| `ASYNC_QUEUE_URL` | SQS queue for async processing |
| `EVENTS_TOPIC_ARN` | SNS topic for events |
