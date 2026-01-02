# Online Banking Platform - Business Logic

## Overview

A commercial bank's next-generation online banking platform using a distributed system architecture. The platform leverages Amazon EC2 for compute resources with Auto Scaling based on Amazon SQS queue depth, ensuring high scalability and cost-effectiveness.

## Business Context

### Problem Statement
The bank needs a highly scalable platform that can:
- Handle variable transaction volumes (peak during business hours, low overnight)
- Process transactions reliably without message loss
- Scale automatically based on demand
- Maintain cost-effectiveness by scaling down during low-demand periods

### Solution Architecture
A distributed messaging system with three main components:
1. **Producers** - API Gateway + Lambda functions that receive banking transactions
2. **Queue** - Amazon SQS for reliable message buffering
3. **Consumers** - Auto-Scaling EC2 instances that process transactions

## System Components

### 1. Transaction Producer (Lambda)

**Purpose**: Receives incoming banking transactions via API Gateway and enqueues them to SQS.

**Transaction Types**:
- `TRANSFER` - Fund transfers between accounts
- `PAYMENT` - Bill payments and external transfers
- `DEPOSIT` - Account deposits
- `WITHDRAWAL` - Account withdrawals
- `BALANCE_CHECK` - Account balance inquiries

**Flow**:
```
Client Request → API Gateway → Lambda Producer → SQS Queue
```

**Validation Rules**:
- Account numbers must be 10-12 digits
- Transfer amounts must be positive
- Currency must be valid ISO 4217 code
- Idempotency key required for duplicate prevention

### 2. Transaction Queue (SQS)

**Configuration**:
- Standard Queue (high throughput, at-least-once delivery)
- Visibility timeout: 60 seconds (time for processing)
- Message retention: 14 days
- Dead Letter Queue for failed messages (max receives: 3)

**Message Format**:
```json
{
  "transaction_id": "uuid",
  "type": "TRANSFER",
  "source_account": "1234567890",
  "target_account": "0987654321",
  "amount": 1000.00,
  "currency": "USD",
  "timestamp": "2024-01-15T10:30:00Z",
  "idempotency_key": "unique-key"
}
```

**Queue Metrics for Scaling**:
- `ApproximateNumberOfMessages` - Messages waiting to be processed
- `ApproximateNumberOfMessagesNotVisible` - Messages being processed
- `ApproximateAgeOfOldestMessage` - Processing latency indicator

### 3. Transaction Processor (EC2 Auto Scaling Group)

**Purpose**: Continuously polls SQS queue and processes banking transactions.

**Architecture**:
- Python Flask application running on EC2
- Multiple worker threads per instance
- Gunicorn WSGI server with multiple workers

**Processing Logic**:
```python
while running:
    messages = sqs.receive_messages(max=10, wait_time=20)
    for message in messages:
        try:
            process_transaction(message)
            message.delete()
        except ProcessingError:
            # Message becomes visible again after timeout
            log_error(message)
```

**Transaction Processing**:
1. Parse and validate message
2. Check for duplicate (idempotency)
3. Verify account exists and has sufficient funds
4. Execute transaction (simulated)
5. Record result in DynamoDB
6. Delete message from queue

### 4. Auto Scaling Configuration

**Scaling Policy**: Target Tracking based on SQS queue depth.

**Scale-Out Trigger**:
- Metric: `ApproximateNumberOfMessages / NumberOfInstances`
- Target: 100 messages per instance
- When queue depth exceeds target → Add instances

**Scale-In Trigger**:
- When queue depth falls below target → Remove instances
- Cooldown period: 300 seconds (prevent thrashing)

**Capacity Limits**:
- Minimum: 2 instances (high availability)
- Maximum: 10 instances (cost control)
- Desired: Dynamic based on queue depth

**Custom Metric Formula**:
```
BacklogPerInstance = ApproximateNumberOfMessages / RunningTaskCount
```

## Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│ API Gateway │────▶│   Lambda    │
│ Application │     │             │     │  Producer   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                    ┌──────────────────────────────────┐
                    │         Amazon SQS Queue         │
                    │  (Transaction Messages Buffer)   │
                    └──────────────────┬───────────────┘
                                       │
                    ┌──────────────────┴───────────────┐
                    │        CloudWatch Alarm          │
                    │  (Queue Depth > Threshold)       │
                    └──────────────────┬───────────────┘
                                       │
                    ┌──────────────────▼───────────────┐
                    │     EC2 Auto Scaling Group       │
                    │ ┌─────────┐ ┌─────────┐ ┌──────┐ │
                    │ │  EC2-1  │ │  EC2-2  │ │ EC2-n│ │
                    │ │Processor│ │Processor│ │ ...  │ │
                    │ └────┬────┘ └────┬────┘ └──┬───┘ │
                    └──────┼───────────┼─────────┼─────┘
                           │           │         │
                           ▼           ▼         ▼
                    ┌──────────────────────────────────┐
                    │         DynamoDB Table           │
                    │    (Transaction Results)         │
                    └──────────────────────────────────┘
```

## Scaling Scenarios

### Scenario 1: Normal Operations
- Queue depth: ~50 messages
- Running instances: 2 (minimum)
- BacklogPerInstance: 25 (below target of 100)
- Action: Maintain minimum capacity

### Scenario 2: Peak Hours
- Queue depth: 500 messages
- Running instances: 2
- BacklogPerInstance: 250 (above target of 100)
- Action: Scale out to 5 instances

### Scenario 3: End of Month Processing
- Queue depth: 2000 messages
- Running instances: 5
- BacklogPerInstance: 400 (above target)
- Action: Scale out to 10 instances (maximum)

### Scenario 4: Off-Peak Hours
- Queue depth: 10 messages
- Running instances: 5
- BacklogPerInstance: 2 (below target)
- Action: Scale in to 2 instances (minimum)

## Error Handling

### Dead Letter Queue (DLQ)
Messages that fail processing 3 times are moved to DLQ for:
- Manual investigation
- Error pattern analysis
- Reprocessing after fixes

### Idempotency
- Each transaction has a unique idempotency key
- DynamoDB stores processed transaction IDs
- Duplicate messages are detected and skipped

### Circuit Breaker
- If DynamoDB errors exceed threshold, pause processing
- Prevents cascading failures
- Auto-recovery after cooldown

## Monitoring & Alerting

### Key Metrics
| Metric | Description | Alarm Threshold |
|--------|-------------|-----------------|
| QueueDepth | Messages waiting | > 1000 |
| OldestMessage | Processing delay | > 5 minutes |
| DLQDepth | Failed messages | > 10 |
| InstanceCount | Running processors | < 2 |
| ProcessingErrors | Errors per minute | > 50 |

### CloudWatch Dashboard
- Real-time queue depth
- Instance count over time
- Transaction processing rate
- Error rate trends

## Cost Optimization

### Auto Scaling Benefits
- Pay only for capacity needed
- Automatic scale-in during low demand
- No over-provisioning

### SQS Pricing
- Per-request pricing (pay per message)
- No minimum fees
- Long polling reduces empty receives

### EC2 Considerations
- Use Spot Instances for cost savings (70% discount)
- Mixed instance types for availability
- Right-size instances based on processing requirements

## Security Considerations

### Network Security
- EC2 instances in private subnets
- VPC endpoints for SQS and DynamoDB
- No public IP addresses on processors

### IAM Permissions
- Least privilege for each component
- Lambda: SendMessage to SQS only
- EC2: ReceiveMessage, DeleteMessage from SQS
- EC2: Read/Write to specific DynamoDB table

### Encryption
- SQS: SSE with KMS
- DynamoDB: Encryption at rest
- Data in transit: TLS 1.3

## Recovery Procedures

### Queue Backlog
If queue depth grows unexpectedly:
1. Check CloudWatch for errors
2. Verify EC2 instances are healthy
3. Manually increase ASG max if needed
4. Review DLQ for processing issues

### DLQ Processing
1. Identify root cause of failures
2. Fix processing logic
3. Redrive messages from DLQ to main queue
4. Monitor for successful processing

### Instance Failure
- ASG automatically replaces unhealthy instances
- Queue messages remain available
- Other instances continue processing
