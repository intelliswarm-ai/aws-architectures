# AWS Architectural Trade-offs & Decision Trees

A collection of decision diagrams to help architects make informed choices when designing AWS solutions. Each diagram maps **keywords/requirements** to **services** with clear reasoning for eliminations.

## How to Use This Guide

1. **Identify the requirement** from stakeholders (cost, performance, availability, etc.)
2. **Find the relevant decision tree** below
3. **Follow the flowchart** based on your specific constraints
4. **Apply elimination rules** to validate your choice

## Decision Diagrams Index

| Category | Diagram | Key Decision Points |
|----------|---------|---------------------|
| [Storage](#storage) | [storage-decisions.md](./diagrams/storage-decisions.md) | S3 vs EFS vs EBS, FSx family, lifecycle, cost |
| [Compute](#compute) | [compute-decisions.md](./diagrams/compute-decisions.md) | Lambda vs Fargate vs EC2, tenancy, recovery |
| [Database](#database) | [database-decisions.md](./diagrams/database-decisions.md) | DynamoDB vs RDS vs Aurora, replication |
| [Messaging](#messaging) | [messaging-decisions.md](./diagrams/messaging-decisions.md) | SQS vs SNS vs Kinesis, ordering |
| [Networking](#networking) | [networking-decisions.md](./diagrams/networking-decisions.md) | ALB vs NLB, NAT, VPC Endpoints |
| [Security](#security) | [security-decisions.md](./diagrams/security-decisions.md) | IAM, SCPs, encryption, API Gateway auth |
| [Caching](#caching) | [caching-decisions.md](./diagrams/caching-decisions.md) | ElastiCache vs DAX vs CloudFront |
| [Scaling](#scaling) | [scaling-decisions.md](./diagrams/scaling-decisions.md) | Auto Scaling policies, placement groups |
| [Migration](#migration) | [migration-decisions.md](./diagrams/migration-decisions.md) | Database migration, hybrid connectivity |
| [Analytics](#analytics) | [analytics-decisions.md](./diagrams/analytics-decisions.md) | Real-time vs batch, data lakes |
| [Containers](#containers) | [containers-decisions.md](./diagrams/containers-decisions.md) | ECS vs EKS, Fargate, IRSA |
| [High Availability](#high-availability) | [high-availability-decisions.md](./diagrams/high-availability-decisions.md) | DR patterns, Multi-AZ, Aurora endpoints |
| [AI & ML](#ai--ml) | [ai-ml-decisions.md](./diagrams/ai-ml-decisions.md) | Comprehend, Textract, Rekognition, Bedrock |

---

## Quick Reference: The 5 Trade-off Questions

Every architectural decision secretly asks one of these:

| Priority | Signal Keywords | Typical AWS Bias |
|----------|-----------------|------------------|
| **Lowest Cost** | "cost-effective", "minimize cost" | Spot, S3, serverless |
| **Highest Availability** | "highly available", "fault tolerant" | Multi-AZ, Global |
| **Lowest Latency** | "real-time", "milliseconds" | Caching, edge, in-memory |
| **Easiest to Manage** | "least operational overhead" | Managed services, serverless |
| **Most Secure** | "compliance", "audit", "encrypt" | KMS, IAM, private endpoints |

---

## Quick Elimination Rules

Use these to quickly eliminate wrong choices:

| If You See... | Eliminate... | Choose... |
|---------------|--------------|-----------|
| "Multiple EC2 shared access" | EBS | EFS or S3 |
| "Least operational overhead" | EC2-based | Managed/serverless |
| "Least privilege" | Wildcard (*) policies | Specific permissions |
| "Exactly-once processing" | Standard SQS | FIFO SQS |
| "UDP + global" | CloudFront | Global Accelerator |
| "Immediate retrieval" | Glacier | Standard-IA |
| "Keys on-premises" | SSE-S3, SSE-KMS | Client-Side Encryption |
| "Predictable spikes" | Target tracking | Scheduled scaling |
| "Root user" | Access keys | MFA + password only |
| "API Gateway + IP filter" | Security groups | Resource policy |
| ">15 min runtime" | Lambda | Containers (Fargate) |
| "AMQP protocol" | SQS | Amazon MQ |
| "SQL Server minimal refactor" | RDS SQL Server | Babelfish |
| "Windows + SMB + AD" | EFS | FSx for Windows |
| "HPC + parallel I/O" | EFS | FSx for Lustre |
| "Multi-protocol NFS+SMB" | FSx Windows | FSx for ONTAP |
| "Cross-region RDS copy" | Read replica | Encrypted snapshot + KMS |
| "Resource configuration history" | CloudTrail | AWS Config |
| "Pod-level AWS permissions" | Node IAM role | IRSA |
| "S3/DynamoDB private access" | Interface Endpoint | Gateway Endpoint (free) |

---

## Categories

### Storage

**Decision Flow:** Access pattern → Durability → Cost

| Requirement | Service |
|-------------|---------|
| Object storage, highest durability | S3 |
| Shared file system (Linux) | EFS |
| Block storage, single EC2 | EBS |
| Windows file shares (SMB/DFS) | FSx for Windows |
| HPC parallel I/O | FSx for Lustre |
| Long-term archive | S3 Glacier |

[View full diagram →](./diagrams/storage-decisions.md)

### Compute

**Decision Flow:** Duration → Concurrency → State

| Requirement | Service |
|-------------|---------|
| < 15 min, event-driven | Lambda |
| Long-running containers, no servers | Fargate |
| Full control, persistent | EC2 |
| Interruptible, cost-sensitive | Spot Instances |
| Predictable, long-term | Reserved Instances |

[View full diagram →](./diagrams/compute-decisions.md)

### Database

**Decision Flow:** Schema → Scale → Latency

| Requirement | Service |
|-------------|---------|
| Schema-less, massive scale | DynamoDB |
| Relational, managed | RDS / Aurora |
| Microsecond reads | DynamoDB + DAX |
| Global replication | Aurora Global / DynamoDB Global Tables |
| In-memory caching | ElastiCache |
| Graph relationships | Neptune |

[View full diagram →](./diagrams/database-decisions.md)

### Messaging

**Decision Flow:** Ordering → Throughput → Pattern

| Requirement | Service |
|-------------|---------|
| Decoupling, buffering | SQS Standard |
| Exactly-once, FIFO | SQS FIFO |
| Fan-out, pub/sub | SNS |
| Streaming, ordering at scale | Kinesis Data Streams |
| Real-time analytics | Kinesis Data Analytics |

[View full diagram →](./diagrams/messaging-decisions.md)

### Networking

**Decision Flow:** Protocol → Geographic reach → Routing needs

| Requirement | Service |
|-------------|---------|
| HTTP/HTTPS, content-based routing | ALB |
| TCP/UDP, extreme performance | NLB |
| Global HTTP caching | CloudFront |
| Global UDP/gaming/real-time | Global Accelerator |
| DNS-based failover | Route 53 |
| Geo-blocking | WAF or CloudFront geo-restriction |

[View full diagram →](./diagrams/networking-decisions.md)

### Security

**Decision Flow:** Resource type → Threat model → Compliance

| Requirement | Service |
|-------------|---------|
| Temporary credentials | IAM Roles |
| DDoS protection | Shield |
| Web app firewall | WAF |
| Secrets storage | Secrets Manager |
| Threat detection | GuardDuty |
| Vulnerability scanning | Inspector |
| Audit trail | CloudTrail |

[View full diagram →](./diagrams/security-decisions.md)

### Containers

**Decision Flow:** Kubernetes needed? → Server management → Storage needs

| Requirement | Service |
|-------------|---------|
| Kubernetes, portability | EKS |
| AWS-native, simple | ECS |
| Serverless containers | Fargate |
| GPU workloads | ECS/EKS on EC2 |
| Pod-level AWS permissions | IRSA |
| On-premises K8s | EKS Anywhere |

[View full diagram →](./diagrams/containers-decisions.md)

### High Availability

**Decision Flow:** RTO/RPO → Cost → Complexity

| Requirement | Service/Pattern |
|-------------|-----------------|
| Lowest cost DR | Backup & Restore |
| Minimal downtime | Warm Standby |
| Zero downtime | Active-Active |
| HA for RDS | Multi-AZ (not Read Replicas) |
| Read scaling | Read Replicas |
| Global Aurora DR | Aurora Global Database |

[View full diagram →](./diagrams/high-availability-decisions.md)

### AI & ML

**Decision Flow:** Task type → ML expertise → Customization

| Requirement | Service |
|-------------|---------|
| Text sentiment, entities | Comprehend |
| Document extraction | Textract |
| Image/video analysis | Rekognition |
| Speech to text | Transcribe |
| Text to speech | Polly |
| Generative AI | Bedrock |
| Custom ML | SageMaker |

[View full diagram →](./diagrams/ai-ml-decisions.md)

---

## Decision-Making Approach

For every architectural decision, follow this approach:

```
1. Identify the goal (what problem are we solving?)
2. Identify the constraint (cost/HA/latency/ops/security)
3. Match keywords to services
4. Eliminate options using elimination rules
5. Pick managed > serverless > scalable
```

> **Architectural principle:** Choose the simplest managed service that meets ALL stated constraints.

---

## Meta-Patterns

### The AWS Architecture Bias

> When AWS provides a **fully managed**, **native**, or **serverless** option — that is almost always the correct answer.

### The Simplicity Rule

> Choose the **simplest managed service** that meets the constraint, not the most flexible one.

### The Compatibility Rule

> "Minimal refactor" usually means **stay within the same ecosystem** (Aurora → Aurora Global, not DynamoDB).

---

## Adding New Decision Trees

This structure is extensible. To add a new decision tree:

1. Create a new file in `diagrams/` following the [TEMPLATE.md](./diagrams/TEMPLATE.md)
2. Add an entry to the index table above
3. Include at minimum:
   - Decision flowchart (Mermaid)
   - Keyword → Service mapping table
   - Elimination rules
   - Real-world examples

---

## Source

These decision trees are synthesized from:
- AWS Well-Architected Framework
- Production architecture reviews
- AWS best practices and service documentation

---

## License

Educational use. Part of the [aws-examples](../) repository.
