# Task Automation System - Business Logic Documentation

This document describes the business logic, data flows, and processing rules for the Serverless Task Automation System built on AWS Lambda with Step Functions orchestration.

## Table of Contents

1. [System Overview](#system-overview)
2. [Task Lifecycle](#task-lifecycle)
3. [Data Flow Architecture](#data-flow-architecture)
4. [Task Generation Logic](#task-generation-logic)
5. [Queue Processing](#queue-processing)
6. [Workflow Orchestration](#workflow-orchestration)
7. [Validation Rules](#validation-rules)
8. [Processing Logic by Task Type](#processing-logic-by-task-type)
9. [Error Handling and Retry Strategy](#error-handling-and-retry-strategy)
10. [Notification System](#notification-system)

---

## System Overview

### Purpose

The Task Automation System demonstrates enterprise-grade serverless patterns:
- Event-driven task generation and processing
- Durable workflow orchestration with Step Functions
- Automatic retry and error handling
- Dead letter queue for failed tasks
- Real-time notifications on completion

### Core Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| Task Generator | Lambda + EventBridge | Create and queue tasks |
| Task Queue | SQS | Buffer tasks for processing |
| Task Worker | Lambda + SQS Trigger | Dequeue and start workflows |
| Workflow | Step Functions | Orchestrate multi-step processing |
| State Store | DynamoDB | Persist task state |
| Notifications | SNS + Lambda | Deliver completion alerts |

---

## Task Lifecycle

### State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TASK STATE TRANSITIONS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                          ┌──────────┐                                       │
│                          │ PENDING  │                                       │
│                          └────┬─────┘                                       │
│                               │ (queued to SQS)                             │
│                               ▼                                             │
│                          ┌──────────┐                                       │
│                          │ QUEUED   │                                       │
│                          └────┬─────┘                                       │
│                               │ (worker picks up)                           │
│                               ▼                                             │
│                         ┌───────────┐                                       │
│                         │IN_PROGRESS│                                       │
│                         └─────┬─────┘                                       │
│                               │ (Step Functions starts)                     │
│                               ▼                                             │
│                         ┌───────────┐                                       │
│                         │VALIDATING │                                       │
│                         └─────┬─────┘                                       │
│                               │                                             │
│              ┌────────────────┼────────────────┐                            │
│              │ (validation    │                │ (validation                │
│              │  failed)       │                │  passed)                   │
│              ▼                │                ▼                            │
│         ┌────────┐            │          ┌───────────┐                      │
│         │ FAILED │            │          │PROCESSING │                      │
│         └────────┘            │          └─────┬─────┘                      │
│                               │                │                            │
│                               │   ┌────────────┼────────────┐               │
│                               │   │ (error,    │            │ (success)     │
│                               │   │  retries   │            │               │
│                               │   │  < max)    │            ▼               │
│                               │   ▼            │      ┌───────────┐         │
│                               │ PENDING        │      │ COMPLETED │         │
│                               │ (retry)        │      └───────────┘         │
│                               │                │                            │
│                               │   (retries     │                            │
│                               │   >= max)      │                            │
│                               │   ▼            │                            │
│                               │ FAILED ◄───────┘                            │
│                               │                                             │
│         ┌───────────┐                                                       │
│         │ CANCELLED │ (manual intervention)                                 │
│         └───────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Status Definitions

| Status | Description |
|--------|-------------|
| `PENDING` | Task created, awaiting queue or retry |
| `QUEUED` | Task sent to SQS |
| `IN_PROGRESS` | Worker processing, workflow started |
| `VALIDATING` | Step Functions validation step active |
| `PROCESSING` | Step Functions processing step active |
| `COMPLETED` | Successfully finished all steps |
| `FAILED` | Processing failed after max retries |
| `CANCELLED` | Manually cancelled by operator |

---

## Data Flow Architecture

### End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TASK PROCESSING PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐                                                           │
│  │ EventBridge  │ (cron: every 5 minutes)                                   │
│  │ Scheduler    │                                                           │
│  └──────┬───────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────┐    ┌──────────────┐                                       │
│  │ Task         │───▶│ SQS Queue    │                                       │
│  │ Generator    │    │              │                                       │
│  │ Lambda       │    │ + Dead       │                                       │
│  │              │    │   Letter Q   │                                       │
│  │ (5 tasks/    │    └──────┬───────┘                                       │
│  │  batch)      │           │                                               │
│  └──────────────┘           │                                               │
│                             ▼                                               │
│                      ┌──────────────┐    ┌──────────────┐                   │
│                      │ Task Worker  │───▶│ Step         │                   │
│                      │ Lambda       │    │ Functions    │                   │
│                      │              │    │              │                   │
│                      │ (batch=10,   │    │ State        │                   │
│                      │  partial     │    │ Machine      │                   │
│                      │  failure)    │    └──────┬───────┘                   │
│                      └──────────────┘           │                           │
│                                                 │                           │
│                   ┌─────────────────────────────┼─────────────────────┐     │
│                   │                             │                     │     │
│                   ▼                             ▼                     ▼     │
│           ┌──────────────┐           ┌──────────────┐       ┌──────────────┐│
│           │ Validate     │           │ Process      │       │ Finalize     ││
│           │ Task         │──────────▶│ Task         │──────▶│ Task         ││
│           │ Lambda       │           │ Lambda       │       │ Lambda       ││
│           └──────────────┘           └──────────────┘       └──────┬───────┘│
│                                                                    │        │
│                                                                    ▼        │
│                      ┌──────────────┐    ┌──────────────┐                   │
│                      │ DynamoDB     │◀───│ SNS Topic    │                   │
│                      │ Task State   │    │ Notifications│                   │
│                      └──────────────┘    └──────┬───────┘                   │
│                                                 │                           │
│                                                 ▼                           │
│                                          ┌──────────────┐                   │
│                                          │ Notification │                   │
│                                          │ Handler      │                   │
│                                          │ Lambda       │                   │
│                                          └──────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Task Generation Logic

### Generator Handler (`TaskGeneratorHandler.java`)

Triggered by EventBridge on a schedule (default: every 5 minutes):

```
┌─────────────────────────────────────────────────────────────────┐
│                    TASK GENERATION FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EventBridge Trigger                                            │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────┐                                            │
│  │ Generate batch  │ (BATCH_SIZE = 5)                           │
│  │ of tasks        │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ For each task:                                              ││
│  │                                                             ││
│  │ 1. Generate UUID                                            ││
│  │ 2. Select random task type                                  ││
│  │ 3. Assign random priority (LOW to CRITICAL)                 ││
│  │ 4. Generate type-specific payload                           ││
│  │ 5. Add metadata (generatedBy, batchIndex, timestamp)        ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Batch send to   │ (max 10 per SQS batch)                     │
│  │ SQS queue       │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Return count    │                                            │
│  │ of queued       │                                            │
│  │ tasks           │                                            │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Task Types and Payloads

| Task Type | Payload Structure | Processing Time |
|-----------|-------------------|-----------------|
| `DATA_PROCESSING` | `{dataSource, recordCount, format}` | 100-500ms |
| `FILE_CLEANUP` | `{directory, pattern, maxAge}` | 50-200ms |
| `REPORT_GENERATION` | `{reportType, format, dateRange}` | 200-800ms |
| `NOTIFICATION_DISPATCH` | `{channel, templateId, recipients}` | 20-100ms |
| `CACHE_REFRESH` | `{cacheType, region, invalidateAll}` | 30-150ms |

### Sample Generated Task

```json
{
  "taskId": "550e8400-e29b-41d4-a716-446655440000",
  "taskType": "DATA_PROCESSING",
  "status": "PENDING",
  "priority": "NORMAL",
  "payload": {
    "dataSource": "s3://data-bucket/input/",
    "recordCount": 10000,
    "format": "JSON"
  },
  "createdAt": "2024-01-15T10:00:00Z",
  "updatedAt": "2024-01-15T10:00:00Z",
  "retryCount": 0,
  "metadata": {
    "generatedBy": "TaskGenerator",
    "batchIndex": 0,
    "timestamp": "2024-01-15T10:00:00Z"
  }
}
```

---

## Queue Processing

### Task Worker Handler (`TaskWorkerHandler.java`)

Processes SQS messages with partial batch failure support:

```
┌─────────────────────────────────────────────────────────────────┐
│                    TASK WORKER FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SQS Trigger (batch_size=10)                                    │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────┐                                            │
│  │ For each        │                                            │
│  │ message:        │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Deserialize Task from message body                          ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Check retry count                                           ││
│  │                                                             ││
│  │ if (retryCount >= MAX_RETRY_COUNT) {                        ││
│  │     throw NonRetryableException("Max retries exceeded")     ││
│  │ }                                                           ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Update task status to IN_PROGRESS in DynamoDB               ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Start Step Functions execution                              ││
│  │                                                             ││
│  │ executionName = "task-{taskId}-{timestamp}"                 ││
│  │ input = WorkflowInput(task, executionId, context)           ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Store execution ARN in task metadata                        ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│     ┌─────┴─────┐                                               │
│     │           │                                               │
│     ▼           ▼                                               │
│  Success    Exception                                           │
│  (delete    (return in                                          │
│   from      SQSBatchResponse                                    │
│   queue)    for retry)                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Partial Batch Failure

The worker implements `SQSBatchResponse` to handle individual message failures:

```java
// Only failed messages are returned to queue
SQSBatchResponse.builder()
    .withBatchItemFailures(failedMessageIds)
    .build();
```

---

## Workflow Orchestration

### Step Functions State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                    STEP FUNCTIONS WORKFLOW                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐                                            │
│  │ Start           │                                            │
│  │ (WorkflowInput) │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ ValidateTask    │ Lambda: validate-task-handler              │
│  │                 │                                            │
│  │ Checks:         │                                            │
│  │ - Required      │                                            │
│  │   fields        │                                            │
│  │ - Payload size  │                                            │
│  │ - Type-specific │                                            │
│  │   rules         │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│     ┌─────┴─────┐                                               │
│     │           │                                               │
│  Success     ValidationError                                    │
│     │           │                                               │
│     │           ▼                                               │
│     │     ┌─────────────────┐                                   │
│     │     │ Fail State      │                                   │
│     │     │ (task → FAILED) │                                   │
│     │     └─────────────────┘                                   │
│     │                                                           │
│     ▼                                                           │
│  ┌─────────────────┐                                            │
│  │ ProcessTask     │ Lambda: process-task-handler               │
│  │                 │                                            │
│  │ Routes to type- │                                            │
│  │ specific logic  │                                            │
│  │ Returns result  │                                            │
│  │ map             │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│     ┌─────┴─────┐                                               │
│     │           │                                               │
│  Success     ProcessingError                                    │
│     │           │                                               │
│     │           ▼                                               │
│     │     ┌─────────────────┐                                   │
│     │     │ Retry with      │                                   │
│     │     │ backoff OR      │                                   │
│     │     │ Fail State      │                                   │
│     │     └─────────────────┘                                   │
│     │                                                           │
│     ▼                                                           │
│  ┌─────────────────┐                                            │
│  │ FinalizeTask    │ Lambda: finalize-task-handler              │
│  │                 │                                            │
│  │ - Set COMPLETED │                                            │
│  │ - Update DB     │                                            │
│  │ - Build summary │                                            │
│  │ - Trigger SNS   │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ End             │                                            │
│  │ (WorkflowOutput)│                                            │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Validation Rules

### Global Validation (`ValidationService.java`)

| Rule | Check | Error Message |
|------|-------|---------------|
| Task ID required | `taskId != null && !taskId.isEmpty()` | "Task ID is required" |
| Task type required | `taskType != null` | "Task type is required" |
| Priority required | `priority != null` | "Priority is required" |
| Payload size | `payload.length() <= 256KB` | "Payload exceeds maximum size" |

### Type-Specific Validation

| Task Type | Required Fields | Validation |
|-----------|-----------------|------------|
| `DATA_PROCESSING` | `dataSource` | Must be non-empty string |
| `REPORT_GENERATION` | `reportType` | Must be valid report type |
| `NOTIFICATION_DISPATCH` | `channel` | Must be EMAIL, SMS, or PUSH |
| `FILE_CLEANUP` | (none additional) | - |
| `CACHE_REFRESH` | (none additional) | - |

---

## Processing Logic by Task Type

### ProcessingService Methods

```
┌─────────────────────────────────────────────────────────────────┐
│                    TASK TYPE PROCESSING                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ DATA_PROCESSING                                             ││
│  │                                                             ││
│  │ Simulated work: 100-500ms                                   ││
│  │ Returns: {                                                  ││
│  │   "recordsProcessed": 100-1100,                             ││
│  │   "processingTimeMs": actual_time                           ││
│  │ }                                                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ FILE_CLEANUP                                                ││
│  │                                                             ││
│  │ Simulated work: 50-200ms                                    ││
│  │ Returns: {                                                  ││
│  │   "filesDeleted": 1-50,                                     ││
│  │   "bytesFreed": calculated                                  ││
│  │ }                                                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ REPORT_GENERATION                                           ││
│  │                                                             ││
│  │ Simulated work: 200-800ms                                   ││
│  │ Returns: {                                                  ││
│  │   "reportId": UUID,                                         ││
│  │   "format": "PDF",                                          ││
│  │   "pageCount": 1-50                                         ││
│  │ }                                                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ NOTIFICATION_DISPATCH                                       ││
│  │                                                             ││
│  │ Simulated work: 20-100ms                                    ││
│  │ Returns: {                                                  ││
│  │   "recipientCount": 1-100,                                  ││
│  │   "channel": from_payload                                   ││
│  │ }                                                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ CACHE_REFRESH                                               ││
│  │                                                             ││
│  │ Simulated work: 30-150ms                                    ││
│  │ Returns: {                                                  ││
│  │   "cacheEntriesRefreshed": 10-1010,                         ││
│  │   "cacheType": from_payload                                 ││
│  │ }                                                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Error Handling and Retry Strategy

### Exception Hierarchy

```
Exception
├── NonRetryableException
│   └── Permanent failures (bad input, not found)
│   └── Message deleted from queue, not retried
│
├── RetryableException
│   └── Transient failures (timeout, throttling)
│   └── Message returned to queue with visibility timeout
│
└── TaskValidationException
    └── Validation failures
    └── Task marked FAILED, no retry
```

### Retry Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `MAX_RETRY_COUNT` | 3 | Maximum processing attempts |
| SQS Visibility Timeout | 60 seconds | Time before retry |
| Step Functions Retry | Exponential backoff | 1s, 2s, 4s |
| DLQ Max Receives | 5 | Then move to Dead Letter Queue |

### Retry Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      RETRY DECISION FLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Exception Thrown                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────┐                                            │
│  │ Exception Type? │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│     ┌─────┴─────────────────┐                                   │
│     │                       │                                   │
│     ▼                       ▼                                   │
│  Retryable           NonRetryable                               │
│     │                       │                                   │
│     ▼                       ▼                                   │
│  ┌─────────────────┐  ┌─────────────────┐                       │
│  │ retryCount++    │  │ Status = FAILED │                       │
│  │ Status = PENDING│  │ Delete message  │                       │
│  │ Return to queue │  │ Log error       │                       │
│  └────────┬────────┘  └─────────────────┘                       │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ retryCount      │                                            │
│  │ >= MAX?         │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│     ┌─────┴─────┐                                               │
│     │           │                                               │
│    No          Yes                                              │
│     │           │                                               │
│     ▼           ▼                                               │
│  Process     Move to DLQ                                        │
│  again       Status = FAILED                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Notification System

### NotificationHandler (`NotificationHandler.java`)

Processes SNS messages for task completion/failure alerts:

```
┌─────────────────────────────────────────────────────────────────┐
│                   NOTIFICATION FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SNS Event                                                      │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────┐                                            │
│  │ Parse SNS       │                                            │
│  │ records         │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Determine notification type from:                           ││
│  │ - Topic ARN (success vs failure topic)                      ││
│  │ - Subject line                                              ││
│  │ - Message attributes                                        ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Parse message body:                                         ││
│  │ - Try JSON parsing                                          ││
│  │ - Fall back to plain text                                   ││
│  │ - Extract taskId, status, summary                           ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Route to notification channels:                             ││
│  │                                                             ││
│  │ if (EMAIL_ENABLED) {                                        ││
│  │     sendEmail(NOTIFICATION_EMAIL, subject, body)            ││
│  │ }                                                           ││
│  │                                                             ││
│  │ if (WEBHOOK_URL != null) {                                  ││
│  │     postToWebhook(WEBHOOK_URL, payload)                     ││
│  │ }                                                           ││
│  │                                                             ││
│  │ log.info("Notification processed", details)                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Notification Channels

| Channel | Configuration | Implementation |
|---------|---------------|----------------|
| Logging | Always enabled | SLF4J INFO level |
| Email | `EMAIL_ENABLED=true` | Amazon SES |
| Webhook | `NOTIFICATION_WEBHOOK_URL` | HTTP POST |

---

## Appendix: Data Models

### Task Entity (DynamoDB)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DYNAMODB TASK SCHEMA                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Partition Key: taskId (String, UUID)                           │
│                                                                 │
│  Attributes:                                                    │
│  ├── taskId: String (UUID)                                      │
│  ├── taskType: String (enum name)                               │
│  ├── status: String (enum name)                                 │
│  ├── priority: String (enum name)                               │
│  ├── payload: String (JSON)                                     │
│  ├── createdAt: String (ISO-8601)                               │
│  ├── updatedAt: String (ISO-8601)                               │
│  ├── scheduledAt: String (ISO-8601, optional)                   │
│  ├── retryCount: Number                                         │
│  ├── lastError: String (optional)                               │
│  ├── metadata: Map<String, String>                              │
│  └── ttl: Number (epoch seconds, 7 days from creation)          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow Input/Output

```java
// WorkflowInput - passed to Step Functions
{
    executionId: String,
    taskId: String,
    task: Task,
    startedAt: Instant,
    context: Map<String, Object>
}

// WorkflowOutput - returned from Step Functions
{
    executionId: String,
    taskId: String,
    task: Task,
    success: boolean,
    message: String,
    completedAt: Instant,
    result: Map<String, Object>
}
```

---

## Appendix: Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TASK_QUEUE_URL` | SQS queue URL | Required |
| `TASK_TABLE_NAME` | DynamoDB table name | Required |
| `STATE_MACHINE_ARN` | Step Functions ARN | Required |
| `NOTIFICATION_EMAIL` | Email recipient | Optional |
| `EMAIL_ENABLED` | Enable email notifications | `false` |
| `NOTIFICATION_WEBHOOK_URL` | Webhook endpoint | Optional |
| `AWS_REGION` | AWS region | `us-east-1` |
