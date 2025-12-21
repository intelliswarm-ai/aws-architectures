# AWS Kinesis - Real-Time GPS Tracking System

A real-time GPS tracking system for delivery trucks using Amazon Kinesis Data Streams.

## Use Case

A company plans to launch an application that tracks the GPS coordinates of delivery trucks in the country. The coordinates are transmitted from each delivery truck every five seconds. The system must be able to process coordinates from multiple consumers in real-time. The aggregated data will be analyzed in a separate reporting application.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  ┌─────────────┐    ┌─────────────────────────────────────┐                    │
│  │ Truck GPS   │    │         Kinesis Data Stream          │                    │
│  │ Simulator   │───▶│  (gps-coordinates-stream)            │                    │
│  │ (Lambda)    │    │  - 4 shards for high throughput      │                    │
│  └─────────────┘    │  - 24hr retention                    │                    │
│                     └───────────────┬─────────────────────┘                    │
│                                     │                                          │
│           ┌─────────────────────────┼─────────────────────────┐                │
│           │                         │                         │                │
│           ▼                         ▼                         ▼                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │ Real-Time       │    │ Geofence        │    │ Archive         │            │
│  │ Dashboard       │    │ Alert           │    │ Processor       │            │
│  │ Consumer        │    │ Consumer        │    │ Consumer        │            │
│  │ (Lambda)        │    │ (Lambda)        │    │ (Lambda)        │            │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘            │
│           │                      │                      │                      │
│           ▼                      ▼                      ▼                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │ DynamoDB        │    │ SNS             │    │ S3              │            │
│  │ (latest pos)    │    │ (alerts)        │    │ (historical)    │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                                          │                     │
│                                                          ▼                     │
│                                                 ┌─────────────────┐            │
│                                                 │ Athena          │            │
│                                                 │ (analytics)     │            │
│                                                 └─────────────────┘            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. GPS Data Producer (Simulator)
- **Lambda Function**: Simulates GPS data from multiple trucks
- **EventBridge Rule**: Triggers every minute to generate batch of coordinates
- **Data Format**: JSON with truck_id, latitude, longitude, speed, heading, timestamp

### 2. Kinesis Data Stream
- **Stream Name**: `gps-coordinates-stream`
- **Shard Count**: 4 (scalable based on throughput needs)
- **Retention**: 24 hours (configurable up to 365 days)
- **Partition Key**: truck_id (ensures ordered processing per truck)

### 3. Real-Time Dashboard Consumer
- **Lambda Function**: Processes coordinates for live dashboard
- **DynamoDB Table**: Stores latest position per truck
- **Use Case**: Fleet management dashboard showing current truck locations

### 4. Geofence Alert Consumer
- **Lambda Function**: Checks if trucks enter/exit defined geofences
- **SNS Topic**: Publishes alerts for geofence violations
- **Use Case**: Notify when trucks deviate from expected routes

### 5. Archive Consumer
- **Lambda Function**: Archives all GPS data for historical analysis
- **S3 Bucket**: Stores data in Parquet format partitioned by date
- **Use Case**: Historical analytics, route optimization, compliance

## Technology Stack

- **Language**: Python 3.12
- **Infrastructure**: Terraform
- **AWS Services**:
  - Amazon Kinesis Data Streams
  - AWS Lambda
  - Amazon DynamoDB
  - Amazon S3
  - Amazon SNS
  - Amazon EventBridge
  - Amazon CloudWatch
  - AWS X-Ray

## Project Structure

```
aws-kinesis/
├── src/
│   ├── common/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration settings
│   │   ├── models.py           # Pydantic data models
│   │   ├── clients.py          # AWS client initialization
│   │   └── exceptions.py       # Custom exceptions
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── gps_producer.py     # GPS data simulator
│   │   ├── dashboard_consumer.py   # Real-time dashboard processor
│   │   ├── geofence_consumer.py    # Geofence alert processor
│   │   └── archive_consumer.py     # S3 archival processor
│   └── services/
│       ├── __init__.py
│       ├── kinesis_service.py  # Kinesis operations
│       ├── geofence_service.py # Geofence calculations
│       └── aggregation_service.py  # Data aggregation
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars
│   └── modules/
│       ├── kinesis/
│       ├── lambda/
│       ├── dynamodb/
│       ├── s3/
│       ├── cloudwatch/
│       └── iam/
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   ├── build.sh
│   ├── deploy.sh
│   └── test.sh
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Prerequisites

- Python 3.12+
- Terraform 1.5+
- AWS CLI configured with appropriate credentials
- Make (optional, for using Makefile)

## Quick Start

### 1. Install Dependencies

```bash
cd aws-kinesis
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

### 3. Run Tests

```bash
./scripts/test.sh
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STREAM_NAME` | Kinesis stream name | `gps-coordinates-stream` |
| `DYNAMODB_TABLE` | DynamoDB table for latest positions | `truck-positions` |
| `S3_BUCKET` | S3 bucket for archived data | `gps-archive-{account_id}` |
| `SNS_TOPIC_ARN` | SNS topic for geofence alerts | - |
| `LOG_LEVEL` | Logging level | `INFO` |

### Geofence Configuration

Geofences are defined in DynamoDB with the following structure:

```json
{
  "geofence_id": "warehouse-001",
  "name": "Main Warehouse",
  "type": "circle",
  "center": {"latitude": 47.3769, "longitude": 8.5417},
  "radius_meters": 500,
  "alert_on": "exit"
}
```

## Data Models

### GPS Coordinate Record

```json
{
  "truck_id": "TRK-001",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "latitude": 47.3769,
  "longitude": 8.5417,
  "speed_kmh": 45.5,
  "heading": 180,
  "altitude_m": 408,
  "accuracy_m": 5,
  "fuel_level_pct": 75,
  "engine_status": "running"
}
```

### Aggregated Statistics (per truck, per hour)

```json
{
  "truck_id": "TRK-001",
  "hour": "2024-01-15T10:00:00Z",
  "total_distance_km": 42.5,
  "average_speed_kmh": 38.2,
  "max_speed_kmh": 85,
  "idle_time_minutes": 12,
  "coordinates_count": 720
}
```

## Scaling Considerations

### Kinesis Shards
- Each shard: 1 MB/sec ingress, 2 MB/sec egress
- 1000 records/sec per shard
- Scale shards based on truck count and data frequency

### Capacity Planning
- 1000 trucks × 1 record/5 sec = 200 records/sec
- Average record size: 500 bytes
- Throughput: ~100 KB/sec
- Recommended: 2 shards (with headroom: 4 shards)

## Monitoring

CloudWatch dashboards include:
- Stream throughput (incoming/outgoing bytes)
- Iterator age (consumer lag)
- Success/failure rates per consumer
- DynamoDB read/write capacity
- Lambda invocations and errors

## Cost Optimization

- Use Enhanced Fan-Out only for consumers requiring sub-200ms latency
- Set appropriate shard count based on actual throughput
- Use S3 Intelligent-Tiering for archived data
- Consider Kinesis Data Firehose for simplified archival

## Multi-Cloud Deployment

This architecture can be implemented on other cloud providers using equivalent services. Below is a mapping of AWS services to their counterparts on Microsoft Azure and Google Cloud Platform.

### Service Mapping

| Component | AWS | Azure | GCP |
|-----------|-----|-------|-----|
| **Stream Ingestion** | Kinesis Data Streams | Event Hubs | Pub/Sub |
| **Stream Processing** | Lambda (Kinesis trigger) | Azure Functions (Event Hub trigger) | Cloud Functions (Pub/Sub trigger) |
| **Serverless Compute** | AWS Lambda | Azure Functions | Cloud Functions / Cloud Run |
| **NoSQL Database** | DynamoDB | Cosmos DB | Firestore / Bigtable |
| **Object Storage** | S3 | Blob Storage | Cloud Storage |
| **Pub/Sub Messaging** | SNS | Service Bus / Event Grid | Pub/Sub |
| **Scheduler** | EventBridge | Logic Apps / Timer Trigger | Cloud Scheduler |
| **Monitoring** | CloudWatch | Azure Monitor | Cloud Monitoring |
| **Tracing** | X-Ray | Application Insights | Cloud Trace |
| **IAM** | IAM Roles/Policies | Azure AD / RBAC | IAM / Service Accounts |
| **IaC** | Terraform / CloudFormation | Terraform / ARM / Bicep | Terraform / Deployment Manager |

### Architecture on Azure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐                │
│  │ Timer Trigger   │    │         Event Hubs               │                │
│  │ Azure Function  │───▶│  (gps-coordinates-hub)           │                │
│  └─────────────────┘    │  - Partitions for throughput     │                │
│                         │  - 24hr retention                 │                │
│                         └───────────────┬─────────────────┘                │
│                                         │                                   │
│           ┌─────────────────────────────┼─────────────────────────┐        │
│           ▼                             ▼                         ▼        │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐ │
│  │ Azure Function  │        │ Azure Function  │        │ Azure Function  │ │
│  │ (Dashboard)     │        │ (Geofence)      │        │ (Archive)       │ │
│  └────────┬────────┘        └────────┬────────┘        └────────┬────────┘ │
│           ▼                          ▼                          ▼          │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐ │
│  │ Cosmos DB       │        │ Service Bus     │        │ Blob Storage    │ │
│  └─────────────────┘        └─────────────────┘        └─────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Azure Considerations:**
- **Event Hubs** uses partitions instead of shards (similar concept)
- **Cosmos DB** with partition key on `truck_id` for scalability
- **Azure Functions** with Event Hub trigger for stream processing
- **Blob Storage** with lifecycle management for tiering to Cool/Archive
- Use **Consumer Groups** for multiple consumers reading the same stream

### Architecture on Google Cloud

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐                │
│  │ Cloud Scheduler │    │         Pub/Sub Topic            │                │
│  │ + Cloud Function│───▶│  (gps-coordinates-topic)         │                │
│  └─────────────────┘    │  - Multiple subscriptions        │                │
│                         │  - 7-day retention               │                │
│                         └───────────────┬─────────────────┘                │
│                                         │                                   │
│           ┌─────────────────────────────┼─────────────────────────┐        │
│           ▼                             ▼                         ▼        │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐ │
│  │ Cloud Function  │        │ Cloud Function  │        │ Cloud Function  │ │
│  │ (Dashboard)     │        │ (Geofence)      │        │ (Archive)       │ │
│  │ Subscription A  │        │ Subscription B  │        │ Subscription C  │ │
│  └────────┬────────┘        └────────┬────────┘        └────────┬────────┘ │
│           ▼                          ▼                          ▼          │
│  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐ │
│  │ Firestore       │        │ Pub/Sub         │        │ Cloud Storage   │ │
│  └─────────────────┘        │ (alerts topic)  │        └─────────────────┘ │
│                             └─────────────────┘                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key GCP Considerations:**
- **Pub/Sub** uses subscriptions for fan-out (each consumer gets its own subscription)
- **Firestore** in Datastore mode for key-value access patterns
- **Cloud Functions** with Pub/Sub trigger (or Cloud Run for containers)
- **Cloud Storage** with Object Lifecycle Management for Nearline/Coldline/Archive
- **Ordering keys** in Pub/Sub ensure per-truck ordering (similar to partition keys)

### Implementation Differences

| Aspect | AWS | Azure | GCP |
|--------|-----|-------|-----|
| **Ordering** | Partition key per shard | Partition key per partition | Ordering key per subscription |
| **Fan-out** | Multiple Lambda consumers | Consumer groups | Multiple subscriptions |
| **Scaling** | Shard splitting | Auto-inflate partitions | Automatic |
| **Retention** | 24h - 365 days | 1 - 90 days | 10 min - 7 days (31 with Lite) |
| **Max Message Size** | 1 MB | 1 MB (256 KB standard) | 10 MB |
| **Throughput** | 1 MB/s per shard | 1 MB/s per TU | Unlimited (quota-based) |

### Terraform Multi-Cloud

This project uses Terraform, which supports all three cloud providers. To deploy on a different cloud:

1. **Azure**: Use `azurerm` provider with equivalent resources:
   ```hcl
   provider "azurerm" {
     features {}
   }

   resource "azurerm_eventhub_namespace" "gps" { ... }
   resource "azurerm_eventhub" "coordinates" { ... }
   resource "azurerm_cosmosdb_account" "positions" { ... }
   ```

2. **GCP**: Use `google` provider with equivalent resources:
   ```hcl
   provider "google" {
     project = var.project_id
     region  = var.region
   }

   resource "google_pubsub_topic" "coordinates" { ... }
   resource "google_pubsub_subscription" "dashboard" { ... }
   resource "google_firestore_database" "positions" { ... }
   ```

### Choosing the Right Platform

| Criteria | Best Choice | Reason |
|----------|-------------|--------|
| **Existing AWS investment** | AWS Kinesis | Native integration, single billing |
| **Microsoft ecosystem** | Azure Event Hubs | Azure AD, Power BI, Dynamics 365 integration |
| **High message volume** | GCP Pub/Sub | Unlimited throughput, simpler pricing |
| **Long retention needed** | AWS Kinesis | Up to 365 days retention |
| **Real-time analytics** | AWS Kinesis + Analytics | Kinesis Data Analytics with SQL/Flink |
| **Cost sensitivity** | GCP Pub/Sub | Pay per message, no provisioned capacity |

## License

This project is licensed under the MIT License.
