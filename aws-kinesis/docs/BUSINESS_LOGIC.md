# GPS Tracking System - Business Logic Documentation

This document describes the business logic, data flows, and processing rules for the Real-Time GPS Tracking System built on Amazon Kinesis Data Streams.

## Table of Contents

1. [System Overview](#system-overview)
2. [Data Flow Architecture](#data-flow-architecture)
3. [GPS Data Generation](#gps-data-generation)
4. [Stream Processing Pipeline](#stream-processing-pipeline)
5. [Geofence Detection Logic](#geofence-detection-logic)
6. [Data Aggregation and Analytics](#data-aggregation-and-analytics)
7. [Storage and Archival](#storage-and-archival)
8. [Monitoring and Alerting](#monitoring-and-alerting)

---

## System Overview

### Purpose

The GPS Tracking System enables logistics companies to:
- Track delivery truck locations in real-time (every 5 seconds)
- Monitor fleet status on live dashboards
- Detect geofence violations (route deviations, restricted area entry)
- Archive historical data for route optimization and compliance
- Generate aggregated statistics for fleet analytics

### Core Business Requirements

| Requirement | Implementation |
|-------------|----------------|
| Real-time tracking (5-sec intervals) | Kinesis Data Stream with 4 shards |
| Multi-consumer processing | Three parallel Lambda consumers |
| Live dashboard updates | DynamoDB with latest positions |
| Geofence alerts | SNS notifications on enter/exit |
| Historical analytics | S3 archive with Parquet partitioning |

### Capacity Planning

```
Fleet Size: 1000 trucks
Update Frequency: 1 record per 5 seconds per truck
Throughput: 200 records/second
Record Size: ~500 bytes
Data Rate: ~100 KB/second
Recommended Shards: 4 (with 20x headroom)
```

---

## Data Flow Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          GPS DATA PIPELINE                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐                                                            │
│  │ EventBridge     │ (every 1 minute)                                           │
│  │ Scheduler       │                                                            │
│  └────────┬────────┘                                                            │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐                 │
│  │ GPS Producer    │───▶│         Kinesis Data Stream         │                 │
│  │ Lambda          │    │  - 4 shards                         │                 │
│  │ (simulates      │    │  - 24hr retention                   │                 │
│  │  truck GPS)     │    │  - Partition key: truck_id          │                 │
│  └─────────────────┘    └───────────────────┬─────────────────┘                 │
│                                             │                                   │
│           ┌─────────────────────────────────┼─────────────────────────┐         │
│           │                                 │                         │         │
│           ▼                                 ▼                         ▼         │
│  ┌─────────────────┐            ┌─────────────────┐        ┌─────────────────┐  │
│  │ Dashboard       │            │ Geofence        │        │ Archive         │  │
│  │ Consumer        │            │ Consumer        │        │ Consumer        │  │
│  │                 │            │                 │        │                 │  │
│  │ Updates latest  │            │ Checks boundary │        │ Stores raw +    │  │
│  │ truck positions │            │ violations      │        │ aggregates      │  │
│  └────────┬────────┘            └────────┬────────┘        └────────┬────────┘  │
│           │                              │                          │           │
│           ▼                              ▼                          ▼           │
│  ┌─────────────────┐            ┌─────────────────┐        ┌─────────────────┐  │
│  │ DynamoDB        │            │ SNS Topic       │        │ S3 Bucket       │  │
│  │ (truck-pos)     │            │ (alerts)        │        │ (archive)       │  │
│  └─────────────────┘            └─────────────────┘        └─────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Partition Key Strategy

All GPS records use `truck_id` as the Kinesis partition key to ensure:
- **Ordered processing**: Records for the same truck arrive in sequence
- **Shard affinity**: Same truck always goes to same shard
- **State management**: Geofence state can be tracked per truck

---

## GPS Data Generation

### Producer Logic (`gps_producer.py`)

The GPS Producer Lambda simulates GPS data from delivery trucks:

```
┌─────────────────────────────────────────────────────────────────┐
│                    GPS PRODUCER FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EventBridge Trigger (every 1 minute)                           │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ For each truck  │ (NUM_TRUCKS = 50 default)                  │
│  │ in fleet        │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Generate 12     │ (simulating 5-sec intervals over 1 min)    │
│  │ GPS coordinates │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Apply movement  │                                            │
│  │ simulation      │                                            │
│  │ - Random delta  │                                            │
│  │ - Speed calc    │                                            │
│  │ - Heading       │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Batch records   │ (100 per batch, max)                       │
│  │ to Kinesis      │                                            │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### GPS Coordinate Generation Rules

| Field | Generation Logic |
|-------|------------------|
| `truck_id` | Format: `TRK-{001..NUM_TRUCKS}` |
| `latitude` | Base location + random delta (±0.001°) |
| `longitude` | Base location + random delta (±0.001°) |
| `speed_kmh` | 0-80 km/h with 10% idle probability |
| `heading` | 0-360° with gradual changes |
| `altitude_m` | Base altitude + small variations |
| `accuracy_m` | 3-10 meters (GPS accuracy simulation) |
| `fuel_level_pct` | Gradual decrease with refueling events |
| `engine_status` | RUNNING (90%), IDLE (10%) |

### Route Simulation

Trucks are assigned to predefined routes based on Swiss cities:

```python
ROUTES = [
    {"name": "Zurich", "lat": 47.3769, "lon": 8.5417},
    {"name": "Bern", "lat": 46.9480, "lon": 7.4474},
    {"name": "Geneva", "lat": 46.2044, "lon": 6.1432},
    {"name": "Basel", "lat": 47.5596, "lon": 7.5886},
    {"name": "Lucerne", "lat": 47.0502, "lon": 8.3093},
]

# Truck assignment: truck_index % len(ROUTES)
```

---

## Stream Processing Pipeline

### Consumer Configuration

All three consumers share common Kinesis event source mapping settings:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Batch Size | 100 | Balance throughput vs latency |
| Parallelization Factor | 10 | 10 concurrent executions per shard |
| Max Batching Window | 5 seconds | Near-real-time with batching efficiency |
| Starting Position | LATEST | Process new events only |
| Bisect on Error | Enabled | Reduce batch size on failures |
| Retry Attempts | 3 | Handle transient failures |
| Max Record Age | 3600 seconds | Skip stale data after 1 hour |

### Dashboard Consumer (`dashboard_consumer.py`)

Updates DynamoDB with the latest position for each truck:

```
┌──────────────────────────────────────────────────────────────────┐
│                 DASHBOARD CONSUMER LOGIC                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  For each GPS coordinate in batch:                               │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                             │
│  │ Parse and       │                                             │
│  │ validate        │                                             │
│  │ coordinate      │                                             │
│  └────────┬────────┘                                             │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                             │
│  │ Group by        │                                             │
│  │ truck_id        │                                             │
│  │ Keep latest     │                                             │
│  │ per truck       │                                             │
│  └────────┬────────┘                                             │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Conditional DynamoDB Write                                  │ │
│  │                                                             │ │
│  │ ConditionExpression:                                        │ │ 
│  │   attribute_not_exists(truck_id)                            │ │
│  │   OR last_update < :new_timestamp                           │ │
│  │                                                             │ │
│  │ Purpose: Prevent out-of-order updates                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                             │
│  │ Set TTL         │ (24 hours from now)                         │
│  │ for auto-       │                                             │
│  │ cleanup         │                                             │
│  └─────────────────┘                                             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Deduplication Strategy

The conditional write prevents race conditions when multiple Lambda instances process the same truck:

```python
# Only update if no existing record OR new timestamp is more recent
condition_expression = (
    "attribute_not_exists(truck_id) OR last_update < :new_update"
)
```

---

## Geofence Detection Logic

### Geofence Types

The system supports two geofence boundary types:

| Type | Detection Method |
|------|------------------|
| **Circle** | Haversine distance from center ≤ radius |
| **Polygon** | Ray casting algorithm for point-in-polygon |

### Geofence Configuration

Geofences are stored in DynamoDB with this structure:

```json
{
  "geofence_id": "warehouse-001",
  "name": "Main Warehouse",
  "geofence_type": "circle",
  "center_latitude": 47.3769,
  "center_longitude": 8.5417,
  "radius_meters": 500,
  "polygon_coordinates": [],
  "alert_on": "exit",
  "active": true
}
```

### Alert Trigger Types

| Setting | Behavior |
|---------|----------|
| `enter` | Alert when truck enters geofence |
| `exit` | Alert when truck leaves geofence |
| `both` | Alert on both enter and exit |

### Geofence Consumer Flow (`geofence_consumer.py`)

```
┌─────────────────────────────────────────────────────────────────┐
│                 GEOFENCE DETECTION FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  For each GPS coordinate:                                       │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Load active     │ (cached with 5-minute TTL)                 │
│  │ geofences from  │                                            │
│  │ DynamoDB        │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ For each        │                                            │
│  │ geofence:       │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Check if coordinate is inside geofence                      ││
│  │                                                             ││
│  │ Circle:                                                     ││
│  │   distance = haversine(coord, center)                       ││
│  │   inside = distance <= radius_meters                        ││
│  │                                                             ││
│  │ Polygon:                                                    ││
│  │   inside = ray_casting(coord, polygon_points)               ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Compare with    │                                            │
│  │ previous state  │ truck_states[truck_id][geofence_id]        │
│  └────────┬────────┘                                            │
│           │                                                     │
│     ┌─────┴─────┐                                               │
│     │           │                                               │
│     ▼           ▼                                               │
│  ┌──────┐   ┌──────┐                                            │
│  │ENTER │   │EXIT  │                                            │
│  │was:  │   │was:  │                                            │
│  │out   │   │in    │                                            │
│  │now:  │   │now:  │                                            │
│  │in    │   │out   │                                            │
│  └──┬───┘   └──┬───┘                                            │
│     │          │                                                │
│     ▼          ▼                                                │
│  ┌─────────────────┐                                            │
│  │ Publish alert   │                                            │
│  │ to SNS if       │                                            │
│  │ alert_on        │                                            │
│  │ matches event   │                                            │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Haversine Distance Calculation

Used for circular geofence boundary detection:

```python
def haversine(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance in meters."""
    R = 6371000  # Earth radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Distance in meters
```

### Geofence Alert Structure

```json
{
  "alert_id": "550e8400-e29b-41d4-a716-446655440000",
  "truck_id": "TRK-001",
  "geofence_id": "warehouse-001",
  "geofence_name": "Main Warehouse",
  "alert_type": "exit",
  "timestamp": "2024-01-15T10:30:00Z",
  "latitude": 47.3769,
  "longitude": 8.5417
}
```

---

## Data Aggregation and Analytics

### Aggregation Service (`aggregation_service.py`)

Calculates fleet statistics for each batch of GPS coordinates:

```
┌──────────────────────────────────────────────────────────────────┐
│                 AGGREGATION CALCULATIONS                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  For each truck in batch:                                        │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Sort coordinates by timestamp                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Calculate Total Distance                                    │ │
│  │                                                             │ │
│  │ for i in range(1, len(coordinates)):                        │ │
│  │     distance += haversine(coords[i-1], coords[i])           │ │
│  │                                                             │ │
│  │ total_distance_km = distance / 1000                         │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Calculate Speed Statistics                                  │ │
│  │                                                             │ │
│  │ average_speed = mean(coord.speed_kmh for coord in coords)   │ │
│  │ max_speed = max(coord.speed_kmh for coord in coords)        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Calculate Idle Time                                         │ │
│  │                                                             │ │ 
│  │ idle_minutes = sum(                                         │ │
│  │     5/60 for coord in coords                                │ │
│  │     if coord.engine_status == "idle"                        │ │
│  │ )                                                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Aggregated Statistics Model

```json
{
  "truck_id": "TRK-001",
  "period_start": "2024-01-15T10:00:00Z",
  "period_end": "2024-01-15T10:05:00Z",
  "total_distance_km": 42.5,
  "average_speed_kmh": 38.2,
  "max_speed_kmh": 85,
  "idle_time_minutes": 12,
  "coordinates_count": 720
}
```

---

## Storage and Archival

### Archive Consumer (`archive_consumer.py`)

Archives both raw GPS data and aggregated statistics to S3:

```
┌─────────────────────────────────────────────────────────────────┐
│                    S3 ARCHIVE STRUCTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  s3://gps-archive-{account_id}/                                 │
│  │                                                              │
│  ├── raw/                                                       │
│  │   └── year=2024/                                             │
│  │       └── month=01/                                          │
│  │           └── day=15/                                        │
│  │               └── 20240115_103000_123456.jsonl               │
│  │                                                              │
│  └── aggregates/                                                │
│      └── year=2024/                                             │
│          └── month=01/                                          │
│              └── day=15/                                        │
│                  └── 20240115_103000_234567.jsonl               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### File Format

Both raw and aggregate files use JSON Lines (JSONL) format:
- One JSON object per line
- Efficient for streaming processing
- Compatible with Athena, Spark, and other analytics tools

### Partitioning Strategy

Date-based partitioning enables:
- **Efficient queries**: Filter by date range in Athena
- **Lifecycle management**: Apply S3 tiering policies by age
- **Cost optimization**: Move old data to Glacier automatically

### S3 Lifecycle Rules

| Age | Storage Class | Use Case |
|-----|---------------|----------|
| 0-30 days | Standard | Active analytics |
| 30-90 days | Intelligent-Tiering | Variable access |
| 90-365 days | Glacier IR | Occasional access |
| 365+ days | Deep Archive | Compliance retention |

---

## Monitoring and Alerting

### CloudWatch Metrics

| Metric | Namespace | Description |
|--------|-----------|-------------|
| IncomingRecords | AWS/Kinesis | Records written to stream |
| IncomingBytes | AWS/Kinesis | Bytes written to stream |
| GetRecords.IteratorAgeMilliseconds | AWS/Kinesis | Consumer lag |
| WriteProvisionedThroughputExceeded | AWS/Kinesis | Throttling events |
| CoordinatesGenerated | GPS/Producer | Custom: records generated |
| CoordinatesSent | GPS/Producer | Custom: records sent |
| PositionsUpdated | GPS/Dashboard | Custom: DynamoDB writes |
| AlertsTriggered | GPS/Geofence | Custom: geofence alerts |
| CoordinatesArchived | GPS/Archive | Custom: S3 records |

### CloudWatch Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| Iterator Age High | > 60 seconds | Consumer falling behind |
| Write Throttling | > 0 | Increase shard count |
| Lambda Errors | > 5 in 5 min | Investigation required |
| Lambda Duration | > 50 sec (of 60) | Optimize or increase timeout |

### Observability Stack

- **Logging**: AWS Lambda Powertools structured logging
- **Tracing**: AWS X-Ray distributed tracing
- **Metrics**: CloudWatch custom metrics via Powertools
- **Dashboards**: Pre-configured CloudWatch dashboard

---

## Appendix: Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STREAM_NAME` | Kinesis stream name | `gps-coordinates-stream` |
| `DYNAMODB_TABLE` | Positions table | `truck-positions` |
| `GEOFENCES_TABLE` | Geofences table | `geofences` |
| `S3_BUCKET` | Archive bucket | `gps-archive-{account}` |
| `SNS_TOPIC_ARN` | Alerts topic | - |
| `NUM_TRUCKS` | Simulated fleet size | `50` |
| `BATCH_SIZE` | Kinesis batch size | `100` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Kinesis Stream Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Shard Count | 4 | Support 4000 records/sec |
| Retention | 24 hours | Balance cost vs replay |
| Encryption | KMS | Security compliance |
| Enhanced Metrics | Enabled | Detailed monitoring |
