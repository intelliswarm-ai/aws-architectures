# Scaling Decision Tree

> **Purpose:** Choose the right AWS scaling strategy based on workload patterns, response time requirements, and cost optimization goals.

## Auto Scaling Policy Decision

```mermaid
flowchart TD
    Start([Scaling Need]) --> Q1{Workload Pattern?}

    Q1 -->|Predictable, time-based| SCHEDULED[Scheduled<br/>Scaling]
    Q1 -->|Keep metric at target| TARGET[Target Tracking<br/>Scaling]
    Q1 -->|React to threshold| STEP[Step/Simple<br/>Scaling]
    Q1 -->|ML-based prediction| PREDICTIVE[Predictive<br/>Scaling]

    SCHEDULED --> USE_SCH[Daily peaks<br/>Weekly patterns<br/>Known events]
    TARGET --> USE_TGT[CPU at 50%<br/>Request count<br/>Queue depth]
    STEP --> USE_STEP[Complex rules<br/>Multiple thresholds]
    PREDICTIVE --> USE_PRED[Traffic forecasting<br/>ML-driven]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef usecase fill:#E6E6FA,stroke:#9370DB,stroke-width:1px
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px

    class Q1 question
    class SCHEDULED,TARGET,STEP,PREDICTIVE service
    class USE_SCH,USE_TGT,USE_STEP,USE_PRED usecase
```

## Target Tracking Metric Decision

```mermaid
flowchart TD
    Start([Target Tracking]) --> Q1{Bottleneck Type?}

    Q1 -->|CPU bound| CPU[ASGAverageCPU<br/>Utilization]
    Q1 -->|Network bound| NETWORK[ASGAverageNetwork<br/>In/Out]
    Q1 -->|Request rate| ALB[ALBRequestCount<br/>PerTarget]
    Q1 -->|Queue depth| CUSTOM[Custom Metric<br/>ApproximateNumberOfMessages]

    CPU --> TARGET_CPU[Target: 40-70%<br/>Higher = more efficient<br/>Lower = more headroom]
    ALB --> TARGET_ALB[Target: Based on<br/>capacity testing]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef config fill:#E6E6FA,stroke:#9370DB,stroke-width:1px
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px

    class Q1 question
    class CPU,NETWORK,ALB,CUSTOM service
    class TARGET_CPU,TARGET_ALB config
```

## Instance Maintenance Decision

```mermaid
flowchart TD
    Start([Instance Maintenance]) --> Q1{During scaling?}

    Q1 -->|Yes, ASG managed| STANDBY[Enter Standby<br/>State]
    Q1 -->|Protect from scale-in| PROTECTION[Scale-in<br/>Protection]
    Q1 -->|Temporarily pause| SUSPEND[Suspend<br/>Processes]

    STANDBY --> DESC_S[Removed from LB<br/>Not replaced<br/>Can return to service]
    PROTECTION --> DESC_P[Won't be terminated<br/>During scale-in]
    SUSPEND --> DESC_SU[Pause specific<br/>scaling activities]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef desc fill:#E6E6FA,stroke:#9370DB,stroke-width:1px
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px

    class Q1 question
    class STANDBY,PROTECTION,SUSPEND service
    class DESC_S,DESC_P,DESC_SU desc
```

## Keyword → Service Mapping

| Keywords / Signals | Scaling Policy | Reasoning |
|--------------------|----------------|-----------|
| predictable spike, monthly sale | Scheduled | Known time-based pattern |
| keep CPU at 50% | Target Tracking | Maintain metric at value |
| complex rules, multiple actions | Step Scaling | Multi-threshold response |
| ML, forecast, proactive | Predictive Scaling | Learn from patterns |
| maintain instance during update | Standby | Temporary removal |
| HPC, low latency | Cluster Placement | Single AZ, high bandwidth |
| fault tolerance, HA | Spread Placement | Across hardware |

## Elimination Rules

| Never Choose | When | Because |
|--------------|------|---------|
| Simple Scaling | Need fine-grained control | One action at a time |
| Target Tracking | Complex multi-threshold rules | Better use Step Scaling |
| Scheduled alone | Unpredictable traffic | Won't respond to real demand |
| Cluster Placement | Need fault tolerance | All instances in same rack |
| Spread Placement | Need lowest latency | Instances physically separated |

## Auto Scaling Policies Comparison

| Policy | Triggers | Best For |
|--------|----------|----------|
| Target Tracking | Metric deviation from target | Most common, simplest |
| Step Scaling | CloudWatch alarm | Complex, multi-threshold |
| Simple Scaling | CloudWatch alarm | Legacy, basic |
| Scheduled | Time-based | Predictable patterns |
| Predictive | ML forecast | Traffic forecasting |

## Target Tracking vs Step Scaling

| Aspect | Target Tracking | Step Scaling |
|--------|-----------------|--------------|
| Configuration | Simple (set target) | Complex (multiple rules) |
| Response | Automatic adjustment | Predefined steps |
| Use Case | Keep metric stable | React to thresholds |
| Example | CPU at 50% | +2 at 60%, +4 at 80% |

## Placement Groups Comparison

| Type | Purpose | Constraint | Use Case |
|------|---------|------------|----------|
| Cluster | Low latency, high throughput | Same AZ, same rack | HPC, ML training |
| Partition | Fault isolation by partition | Up to 7 partitions/AZ | HDFS, Cassandra |
| Spread | Maximum fault tolerance | Max 7 instances/AZ | Critical instances |

## Cost Optimization Strategies

| Strategy | Implementation | Savings |
|----------|----------------|---------|
| Scheduled scale-down | Scale to 0 off-hours | 50-70% |
| Mixed instances | On-Demand + Spot | 50-70% |
| Right-sizing | Smaller instances, more of them | Variable |
| Predictive scaling | Pre-warm before spike | Better UX |

## Trade-off Matrix

| Aspect | Target Tracking | Step Scaling | Scheduled |
|--------|-----------------|--------------|-----------|
| Complexity | Low | High | Low |
| Responsiveness | Good | Best | N/A |
| Predictability | Medium | High | High |
| Cost Control | Medium | High | High |
| Use Case | General | Complex | Time-based |

## Real-World Scenarios

### Scenario 1: Keep CPU Around 50%
**Requirement:** Maintain application performance near 50% CPU
**Decision:** Target Tracking with CPU utilization target 50%
**Reasoning:** Automatic adjustment to maintain target

### Scenario 2: Daily Traffic Spike at 9 AM
**Requirement:** Handle known morning traffic surge
**Decision:** Scheduled Scaling (scale up at 8:45 AM)
**Reasoning:** Predictable pattern, pre-warm instances

### Scenario 3: HPC Workload
**Requirement:** Minimize latency between compute nodes
**Decision:** Cluster Placement Group
**Reasoning:** All instances in single rack, low latency

### Scenario 4: Critical Application HA
**Requirement:** No single point of hardware failure
**Decision:** Spread Placement Group
**Reasoning:** Each instance on different hardware

### Scenario 5: Instance Patching
**Requirement:** Patch one instance without ASG replacing it
**Decision:** Enter Standby state
**Reasoning:** Removed from LB, not replaced, can return

### Scenario 6: SQS-Based Worker Scaling
**Requirement:** Scale workers based on queue depth
**Decision:** Target Tracking with custom metric (BacklogPerInstance)
**Reasoning:** Scale based on messages per worker

## SQS-Based Scaling

```
Custom Metric: BacklogPerInstance = ApproximateNumberOfMessages / RunningInstances
Target: Based on acceptable backlog per worker
```

| Metric | Calculation |
|--------|-------------|
| Queue messages | CloudWatch ApproximateNumberOfMessages |
| Running instances | ASG GroupInServiceInstances |
| Backlog per instance | Messages / Instances |

## Common Mistakes

1. **Mistake:** Using Simple Scaling for production workloads
   **Correct approach:** Use Target Tracking or Step Scaling

2. **Mistake:** Scheduled scaling for unpredictable traffic
   **Correct approach:** Combine with Target Tracking

3. **Mistake:** Setting target too high (90% CPU)
   **Correct approach:** 40-70% allows headroom for spikes

4. **Mistake:** Cluster placement for HA requirements
   **Correct approach:** Spread placement for fault tolerance

5. **Mistake:** Deleting instance during maintenance
   **Correct approach:** Use Standby state to preserve and return

## Scaling Cooldown Periods

| Scenario | Cooldown Purpose |
|----------|------------------|
| Scale-out | Prevent over-scaling |
| Scale-in | Prevent aggressive termination |
| Default | 300 seconds |

> **Tip:** Target Tracking manages cooldowns automatically

## ASG Lifecycle Hooks

| Hook | Use Case |
|------|----------|
| Pending:Wait | Configure instance before in-service |
| Terminating:Wait | Drain connections before termination |

## Related Decisions

- [Compute Decisions](./compute-decisions.md) - EC2 instance types
- [Networking Decisions](./networking-decisions.md) - Load balancer health checks
- [Messaging Decisions](./messaging-decisions.md) - SQS-based scaling

---

## Quick Reference

1. **Predictable spikes** → Scheduled Scaling
2. **Keep metric at target** → Target Tracking
3. **Complex thresholds** → Step Scaling
4. **ML-based forecast** → Predictive Scaling
5. **HPC / low latency** → Cluster Placement Group
6. **Fault tolerance** → Spread Placement Group
7. **Maintenance without replacement** → Standby State
8. **SQS scaling** → Custom metric (BacklogPerInstance)
