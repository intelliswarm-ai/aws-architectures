# ML Canary Deployment - Business Logic

## System Overview

This system enables zero-downtime ML model deployments for a media streaming company serving 50 million daily active users. It uses SageMaker production variants with traffic splitting to gradually shift traffic from the current model to a new version while monitoring performance metrics.

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CANARY DEPLOYMENT FLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

1. DEPLOYMENT INITIATION
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │  User/CI/CD  │───▶│  API Gateway │───▶│  Deployment  │
   │   Request    │    │   /deploy    │    │   Handler    │
   └──────────────┘    └──────────────┘    └──────────────┘
                                                  │
                                                  ▼
   ┌──────────────────────────────────────────────────────┐
   │  1. Create new endpoint config with canary variant   │
   │  2. Update endpoint to new config                    │
   │  3. Store deployment record in DynamoDB              │
   │  4. Send deployment started notification             │
   └──────────────────────────────────────────────────────┘

2. TRAFFIC SPLITTING (Initial: 90% Production / 10% Canary)
   ┌─────────────────────────────────────────────────────────────────────┐
   │                      SageMaker Endpoint                             │
   │  ┌─────────────────────────────────────────────────────────────┐   │
   │  │                    Request Router                            │   │
   │  │                                                              │   │
   │  │   Incoming    ┌──────────────────────────────────────────┐  │   │
   │  │   Request ───▶│     Weight-Based Traffic Distribution     │  │   │
   │  │               └────────────┬──────────────┬──────────────┘  │   │
   │  │                            │              │                  │   │
   │  │                     90% ───┘              └─── 10%           │   │
   │  │                            │              │                  │   │
   │  │                            ▼              ▼                  │   │
   │  │                  ┌──────────────┐  ┌──────────────┐         │   │
   │  │                  │  Production  │  │   Canary     │         │   │
   │  │                  │   Variant    │  │   Variant    │         │   │
   │  │                  │  (Current)   │  │  (New Model) │         │   │
   │  │                  └──────────────┘  └──────────────┘         │   │
   │  └─────────────────────────────────────────────────────────────┘   │
   └─────────────────────────────────────────────────────────────────────┘

3. MONITORING LOOP (Every Minute)
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │  EventBridge │───▶│  Monitoring  │───▶│  CloudWatch  │
   │   Schedule   │    │   Handler    │    │   Metrics    │
   └──────────────┘    └──────────────┘    └──────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────┐
   │  HEALTH EVALUATION                                       │
   │  ┌─────────────────────────────────────────────────┐    │
   │  │  Canary Metrics:                                 │    │
   │  │    - P99 Latency: 45ms ✓ (< 100ms threshold)    │    │
   │  │    - Error Rate: 0.5% ✓ (< 1% threshold)        │    │
   │  │    - Invocations: 5,000                         │    │
   │  └─────────────────────────────────────────────────┘    │
   │                           │                              │
   │                           ▼                              │
   │  ┌─────────────────────────────────────────────────┐    │
   │  │  Comparison with Production:                     │    │
   │  │    - Latency Ratio: 1.1x ✓ (< 2x)               │    │
   │  │    - Error Rate Diff: +0.2% ✓ (< 5%)            │    │
   │  └─────────────────────────────────────────────────┘    │
   └─────────────────────────────────────────────────────────┘

4. PROGRESSIVE TRAFFIC SHIFT
   ┌─────────────────────────────────────────────────────────────────────┐
   │  Canary healthy → Increase traffic by step size (default 10%)       │
   │                                                                      │
   │  Time 0:     Production 90% │████████████████████████████████████│  │
   │              Canary     10% │████                                │  │
   │                                                                      │
   │  Time +10m:  Production 80% │████████████████████████████████    │  │
   │              Canary     20% │████████                            │  │
   │                                                                      │
   │  Time +20m:  Production 70% │████████████████████████████        │  │
   │              Canary     30% │████████████                        │  │
   │                                                                      │
   │  ...continues until canary reaches 100%...                          │
   │                                                                      │
   │  Complete:   Production  0% │                                    │  │
   │              Canary    100% │████████████████████████████████████│  │
   └─────────────────────────────────────────────────────────────────────┘

5. AUTO-ROLLBACK (If thresholds exceeded)
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │  Monitoring  │───▶│   Rollback   │───▶│  SageMaker   │
   │   Handler    │    │   Handler    │    │  API Call    │
   └──────────────┘    └──────────────┘    └──────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────┐
   │  UpdateEndpointWeightsAndCapacities:                    │
   │    - Production Variant Weight: 1.0 (100%)              │
   │    - Canary Variant Weight: 0.0 (0%)                    │
   │                                                          │
   │  Result: Immediate traffic shift to production           │
   │          No endpoint downtime                            │
   └─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Deployment Service

Manages the lifecycle of canary deployments:

```
CREATE DEPLOYMENT:
1. Validate endpoint exists and is InService
2. Create new endpoint config with canary variant
3. Call UpdateEndpoint with new config
4. Store deployment record in DynamoDB
5. Send SNS notification

COMPLETE DEPLOYMENT:
1. Set canary weight to 100%
2. Update deployment status to COMPLETED
3. Optionally remove old production variant

CANCEL DEPLOYMENT:
1. Set canary weight to 0%
2. Update deployment status to CANCELLED
3. Clean up canary variant
```

### 2. Traffic Service

Manages traffic distribution using `UpdateEndpointWeightsAndCapacities`:

```python
# Key API call for traffic shifting
sagemaker.update_endpoint_weights_and_capacities(
    EndpointName=endpoint_name,
    DesiredWeightsAndCapacities=[
        {
            "VariantName": "production",
            "DesiredWeight": 0.8  # 80% traffic
        },
        {
            "VariantName": "canary",
            "DesiredWeight": 0.2  # 20% traffic
        }
    ]
)
```

This API allows:
- Instant traffic weight changes (no endpoint downtime)
- Gradual traffic shifts over time
- Immediate rollback by setting weights

### 3. Monitoring Service

Collects CloudWatch metrics for evaluation:

```
METRICS COLLECTED:
├── Invocations (Sum)
├── Invocation4XXErrors (Sum)
├── Invocation5XXErrors (Sum)
├── ModelLatency (p50, p90, p99)
├── OverheadLatency (Average)
├── CPUUtilization (Average)
└── MemoryUtilization (Average)

HEALTH EVALUATION:
├── P99 Latency < threshold (100ms)
├── Error Rate < threshold (1%)
├── Latency ratio vs production < 2x
└── Error rate diff vs production < 5%
```

### 4. Inference Service

Handles real-time inference requests:

```
REQUEST FLOW:
1. Receive request from API Gateway
2. Validate request body (user_id, features)
3. Invoke SageMaker endpoint
4. SageMaker routes to variant based on weights
5. Return predictions with variant info

LATENCY TARGETS:
- Model inference: < 50ms
- Total request: < 100ms (including network, Lambda overhead)
```

## Deployment States

```
┌─────────┐    ┌─────────────┐    ┌───────────┐    ┌───────────┐
│ PENDING │───▶│ IN_PROGRESS │───▶│ COMPLETED │    │  FAILED   │
└─────────┘    └─────────────┘    └───────────┘    └───────────┘
                     │                                    ▲
                     │ (threshold exceeded)               │
                     ▼                                    │
              ┌──────────────┐    ┌─────────────┐        │
              │ ROLLING_BACK │───▶│ ROLLED_BACK │────────┘
              └──────────────┘    └─────────────┘
```

## Error Handling

### Retryable Errors
- Service temporarily unavailable
- Throttling exceptions
- Network timeouts

### Non-Retryable Errors
- Validation errors (invalid input)
- Endpoint not found
- Variant not found
- Model errors

### Auto-Rollback Triggers
1. P99 latency exceeds threshold for 3 consecutive checks
2. Error rate exceeds threshold for 2 consecutive checks
3. Canary metrics significantly worse than production

## Scaling Strategy

### Auto-Scaling Configuration
```
Target Tracking Scaling:
- Metric: SageMakerVariantInvocationsPerInstance
- Target: 1000 invocations per instance
- Scale Out Cooldown: 60 seconds
- Scale In Cooldown: 300 seconds
- Min Capacity: 1
- Max Capacity: 10
```

### Scaling Behavior
```
Traffic Pattern:
┌────────────────────────────────────────────────────────────┐
│  Invocations │                    ╱╲                       │
│              │                   ╱  ╲                      │
│     Peak     │                  ╱    ╲                     │
│              │    ╱╲           ╱      ╲           ╱╲       │
│     Normal   │   ╱  ╲         ╱        ╲         ╱  ╲      │
│              │  ╱    ╲       ╱          ╲       ╱    ╲     │
│     Base     │ ╱      ╲     ╱            ╲     ╱      ╲    │
│              │╱        ╲___╱              ╲___╱        ╲   │
├──────────────┴─────────────────────────────────────────────┤
│              6am       12pm       6pm      12am      6am   │
└────────────────────────────────────────────────────────────┘

Instance Count:
- Base: 2 instances
- Peak: 10 instances (scales based on invocations)
```

## Best Practices

1. **Start with small canary weight** (5-10%)
2. **Use bake time** between traffic shifts (10+ minutes)
3. **Enable auto-rollback** for production deployments
4. **Monitor both variants** for comparison
5. **Set realistic thresholds** based on baseline metrics
6. **Use staged rollouts** (dev → staging → prod)
