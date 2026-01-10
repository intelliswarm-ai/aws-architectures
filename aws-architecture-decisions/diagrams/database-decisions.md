# Database Decision Tree

> **Purpose:** Choose the right AWS database service based on data model, scale requirements, latency needs, and operational complexity.

## Decision Flowchart

```mermaid
flowchart TD
    Start([Database Requirement]) --> Q1{Data Model?}

    Q1 -->|Relational/SQL| Q2{Need Aurora<br/>compatibility?}
    Q1 -->|Key-Value/Document| Q3{Scale requirement?}
    Q1 -->|Graph| NEPTUNE[Amazon Neptune]
    Q1 -->|Time-series| TIMESTREAM[Amazon Timestream]
    Q1 -->|Ledger/Immutable| QLDB[Amazon QLDB]

    Q2 -->|Yes, MySQL/PostgreSQL| Q4{Global distribution?}
    Q2 -->|No, other engines| RDS[Amazon RDS]

    Q4 -->|Yes| AURORA_GLOBAL[Aurora Global<br/>Database]
    Q4 -->|No| AURORA[Amazon Aurora]

    Q3 -->|Massive, serverless| DYNAMO[DynamoDB]
    Q3 -->|Moderate, more flexibility| DOCDB[DocumentDB]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px,color:#000000
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:#000000
    classDef start fill:#ADD8E6,stroke:#4169E1,stroke-width:2px

    class Start start
    class Q1,Q2,Q3,Q4 question
    class NEPTUNE,TIMESTREAM,QLDB,RDS,AURORA_GLOBAL,AURORA,DYNAMO,DOCDB service
```

## Replication Decision

```mermaid
flowchart TD
    Start([Replication Need]) --> Q1{Primary Goal?}

    Q1 -->|High Availability| MULTI_AZ[Multi-AZ<br/>Synchronous]
    Q1 -->|Read Scaling| READ_REPLICA[Read Replicas<br/>Asynchronous]
    Q1 -->|Disaster Recovery| Q2{Geographic scope?}

    Q2 -->|Same Region| READ_REPLICA
    Q2 -->|Cross-Region| CROSS_REGION[Cross-Region<br/>Read Replica]

    MULTI_AZ --> DESC1[Automatic failover<br/>Same region<br/>Sync replication]
    READ_REPLICA --> DESC2[Read scaling<br/>Async replication<br/>Can promote]
    CROSS_REGION --> DESC3[DR capability<br/>Async replication<br/>Higher latency]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px,color:#000000
    classDef desc fill:#E6E6FA,stroke:#9370DB,stroke-width:1px,color:#000000
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:#000000

    class Q1,Q2 question
    class MULTI_AZ,READ_REPLICA,CROSS_REGION service
    class DESC1,DESC2,DESC3 desc
```

## DynamoDB vs RDS Decision

```mermaid
flowchart TD
    Start([Database Choice]) --> Q1{Schema flexibility?}

    Q1 -->|Fixed schema, relationships| Q2{Query complexity?}
    Q1 -->|Flexible, key-value| Q3{Access pattern?}

    Q2 -->|Complex JOINs| RDS[RDS / Aurora<br/>Relational]
    Q2 -->|Simple queries| Q3

    Q3 -->|Known, predictable| DYNAMO[DynamoDB]
    Q3 -->|Ad-hoc queries| RDS

    DYNAMO --> Q4{Read latency?}
    Q4 -->|Milliseconds OK| DYNAMO_STD[DynamoDB<br/>Standard]
    Q4 -->|Microseconds needed| DAX[DynamoDB<br/>+ DAX]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px,color:#000000
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:#000000

    class Q1,Q2,Q3,Q4 question
    class RDS,DYNAMO,DYNAMO_STD,DAX service
```

## Keyword → Service Mapping

| Keywords / Signals | AWS Service | Reasoning |
|--------------------|-------------|-----------|
| relational, SQL, ACID, joins | RDS / Aurora | Full SQL support |
| schema-less, massive scale | DynamoDB | Single-digit ms at any scale |
| microsecond latency, leaderboard | DynamoDB + DAX | In-memory caching |
| MySQL/PostgreSQL, 5x performance | Aurora | AWS-optimized engine |
| global reads, < 1 second RPO | Aurora Global Database | Cross-region replication |
| global tables, active-active | DynamoDB Global Tables | Multi-region writes |
| MongoDB compatibility | DocumentDB | Managed MongoDB API |
| graph, relationships | Neptune | Graph queries |
| IoT, time-series | Timestream | Built-in time functions |
| blockchain, immutable | QLDB | Cryptographic verification |

## Elimination Rules

| Never Choose | When | Because |
|--------------|------|---------|
| DynamoDB | Complex ad-hoc queries needed | No JOIN support, access patterns must be known |
| RDS | Need unlimited scale | Has scaling limits |
| Single-AZ RDS | High availability required | No automatic failover |
| Read Replica | Need sync replication | Read replicas are async |
| Aurora | Need Oracle/SQL Server | Only MySQL/PostgreSQL compatible |

## High Availability vs Read Scaling

| Feature | Multi-AZ | Read Replicas |
|---------|----------|---------------|
| Purpose | High Availability | Read Scaling |
| Replication | Synchronous | Asynchronous |
| Failover | Automatic | Manual promotion |
| Read Traffic | No | Yes |
| Regions | Same region | Same or cross-region |
| Data Lag | Zero | Seconds to minutes |

> **Key Insight:** Multi-AZ = HA (sync) | Read Replicas = Scale/DR (async)

## Cost Comparison

| Service | Pricing Model | Best For |
|---------|---------------|----------|
| DynamoDB On-Demand | Pay per request | Variable workloads |
| DynamoDB Provisioned | Capacity units | Predictable workloads |
| RDS | Instance hours + storage | Traditional workloads |
| Aurora | Instance hours + I/O | High performance SQL |
| Aurora Serverless | ACUs consumed | Variable SQL workloads |

## Trade-off Matrix

| Aspect | DynamoDB | RDS | Aurora | DocumentDB |
|--------|----------|-----|--------|------------|
| Scale | Unlimited | Limited | High | High |
| Latency | Single-digit ms | ms | ms | ms |
| Schema | Flexible | Fixed | Fixed | Flexible |
| Queries | Key-based | SQL | SQL | MongoDB API |
| Ops | Zero | Medium | Low | Low |
| Cost (small) | Low | Medium | Higher | Medium |
| Cost (large) | Variable | Predictable | Predictable | Predictable |

## Real-World Scenarios

### Scenario 1: E-commerce Product Catalog
**Requirement:** Variable traffic, simple lookups by product ID
**Decision:** DynamoDB
**Reasoning:** Key-value access, auto-scaling, serverless

### Scenario 2: Financial Application with Complex Reporting
**Requirement:** ACID transactions, complex JOINs, audit trails
**Decision:** Aurora PostgreSQL with Multi-AZ
**Reasoning:** Full SQL, HA, strong consistency

### Scenario 3: Gaming Leaderboard
**Requirement:** Microsecond reads, global players
**Decision:** DynamoDB + DAX + Global Tables
**Reasoning:** DAX for microsecond cache, global tables for multi-region

### Scenario 4: Social Network Connections
**Requirement:** Find friends-of-friends, relationship queries
**Decision:** Amazon Neptune
**Reasoning:** Graph database optimized for relationship traversal

### Scenario 5: IoT Sensor Data
**Requirement:** Time-series data, built-in analytics
**Decision:** Amazon Timestream
**Reasoning:** Purpose-built for time-series, automatic tiering

### Scenario 6: SQL Server Migration (Minimal Refactor)
**Requirement:** Migrate SQL Server to AWS with minimal code changes
**Decision:** Babelfish for Aurora PostgreSQL + AWS SCT/DMS
**Reasoning:** Babelfish understands T-SQL, minimal application changes

## DynamoDB Access Patterns

| Access Pattern | Design Approach |
|----------------|-----------------|
| Single item by key | Partition key lookup |
| Items by partition | Query on partition key |
| Multiple access patterns | GSI (Global Secondary Index) |
| Hierarchical data | Composite sort key |
| Many-to-many | Adjacency list pattern |

## Common Mistakes

1. **Mistake:** Using DynamoDB for ad-hoc analytics queries
   **Correct approach:** Use RDS/Athena for complex queries

2. **Mistake:** Relying on Read Replicas for HA
   **Correct approach:** Use Multi-AZ for automatic failover

3. **Mistake:** Choosing RDS when scale is unpredictable
   **Correct approach:** Use DynamoDB or Aurora Serverless

4. **Mistake:** Forgetting DAX for read-heavy DynamoDB
   **Correct approach:** Add DAX for microsecond caching

5. **Mistake:** Using DynamoDB without planning access patterns
   **Correct approach:** Design GSIs based on query patterns upfront

## Aurora vs RDS Decision

| Choose Aurora When | Choose RDS When |
|--------------------|-----------------|
| MySQL/PostgreSQL and need 5x performance | Need Oracle, SQL Server, MariaDB |
| Auto-scaling storage needed | Fixed, predictable storage |
| Fast failover (< 30s) | Standard failover OK |
| Up to 15 read replicas | Up to 5 read replicas |
| Cross-region global database | Simpler setup |

## Related Decisions

- [Caching Decisions](./caching-decisions.md) - DAX vs ElastiCache
- [Migration Decisions](./migration-decisions.md) - Database migration strategies
- [Storage Decisions](./storage-decisions.md) - Data lake vs database

---

## Quick Reference

1. **Schema-less + scale** → DynamoDB
2. **Complex SQL + JOINs** → RDS / Aurora
3. **Microsecond reads** → DynamoDB + DAX
4. **Global reads, low latency** → Aurora Global / DynamoDB Global Tables
5. **Multi-AZ** = HA (sync) | **Read Replica** = Scale (async)
6. **Graph queries** → Neptune
7. **Time-series** → Timestream
8. **"Minimal refactor" from SQL Server** → Babelfish + Aurora PostgreSQL
