# AWS Architectures Reference

A collection of AWS architectures demonstrating best practices for cloud-native and hybrid application development. Each project showcases different AWS services, patterns, and implementation approaches including serverless, PaaS, and hybrid cloud architectures.

## Author

Created by **Theodoros Messinis**, AWS Certified Solutions Architect.

[![AWS Certified Solutions Architect](https://images.credly.com/size/110x110/images/0e284c3f-5164-4b21-8660-0d84737941bc/image.png)](https://www.credly.com/users/theodoros-messinis/badges)

- [LinkedIn](https://www.linkedin.com/in/messinis/)
- [AWS Certifications (Credly)](https://www.credly.com/users/theodoros-messinis/badges)

## Disclaimer

This project is not officially supported by Amazon Web Services (AWS). It is a product of individual research. The architectures and code examples provided here represent personal interpretations of AWS best practices.

---

## Projects

| Project | Description | Language | Key AWS Services | Business Logic |
|---------|-------------|----------|------------------|----------------|
| [serverless-api](./serverless-api) | Task Automation System | Java 21 | Lambda, SQS, DynamoDB, Step Functions | [docs](./serverless-api/docs/BUSINESS_LOGIC.md) |
| [document-processing](./document-processing) | Intelligent Document Processing | Python 3.12 | SageMaker, Bedrock, Textract, Comprehend | [docs](./document-processing/docs/BUSINESS_LOGIC.md) |
| [multi-tenant-saas](./multi-tenant-saas) | Multi-Tenant SaaS Platform (intelliswarm.ai) | Python 3.12 | Cognito, WAF, KMS, VPC, Bedrock, CloudTrail | [docs](./multi-tenant-saas/docs/BUSINESS_LOGIC.md) |
| [fleet-tracking](./fleet-tracking) | Real-Time GPS Tracking System | Python 3.12 | Kinesis Data Streams, Lambda, DynamoDB, S3 | [docs](./fleet-tracking/docs/BUSINESS_LOGIC.md) |
| [messaging-platform](./messaging-platform) | SMS Marketing Campaign Platform | Python 3.12 | Pinpoint, Kinesis, Lambda, DynamoDB, S3 | [docs](./messaging-platform/docs/BUSINESS_LOGIC.md) |
| [banking-transactions](./banking-transactions) | Online Banking Platform with SQS Auto Scaling | Python 3.12 | SQS, EC2 Auto Scaling, DynamoDB, CloudWatch | [docs](./banking-transactions/docs/BUSINESS_LOGIC.md) |
| [call-center-analytics](./call-center-analytics) | Call Center Sentiment Analysis | Python 3.12 | Comprehend, OpenSearch, Lambda, S3, API Gateway | [docs](./call-center-analytics/docs/BUSINESS_LOGIC.md) |
| [conversational-ai](./conversational-ai) | Airline Chatbot Platform | Python 3.12 | Lex V2, Lambda, DynamoDB, API Gateway | [docs](./conversational-ai/docs/BUSINESS_LOGIC.md) |
| [data-lake-analytics](./data-lake-analytics) | Data Lake Analytics Platform | Python 3.12 | Athena, Glue, Lake Formation, S3 | [docs](./data-lake-analytics/docs/BUSINESS_LOGIC.md) |
| [hybrid-enterprise-app](./hybrid-enterprise-app) | Hybrid Enterprise Inventory System | Java 21 | Elastic Beanstalk, VPN Gateway, S3, CloudWatch | [docs](./hybrid-enterprise-app/docs/BUSINESS_LOGIC.md) |
| [emr-fraud-detection](./emr-fraud-detection) | ML Fraud Detection with Spark | Python 3.12 | EMR, Spark MLlib, Kinesis, Step Functions, DynamoDB | [docs](./emr-fraud-detection/docs/BUSINESS_LOGIC.md) |
| [genai-knowledge-assistant](./genai-knowledge-assistant) | RAG Knowledge Base Assistant | Python 3.12 | Bedrock (Claude, Titan), Knowledge Bases, Agents, OpenSearch Serverless | [docs](./genai-knowledge-assistant/docs/BUSINESS_LOGIC.md) |
| [healthcare-imaging-lake](./healthcare-imaging-lake) | HIPAA-Compliant Healthcare Imaging Data Lake | Python 3.12 | S3, KMS, Glue, Lake Formation, Athena, Lambda | [docs](./healthcare-imaging-lake/docs/BUSINESS_LOGIC.md) |
| [secure-ml-transformation](./secure-ml-transformation) | Secure ML Data Transformation Pipeline | Python 3.12 | Glue ETL, DataBrew, VPC Endpoints, KMS, CloudWatch | [docs](./secure-ml-transformation/docs/BUSINESS_LOGIC.md) |
| [ml-canary-deployment](./ml-canary-deployment) | ML Canary Deployment with Traffic Splitting | Python 3.12 | SageMaker, Lambda, API Gateway, DynamoDB, CloudWatch | [docs](./ml-canary-deployment/docs/BUSINESS_LOGIC.md) |

---

## Technology Quick Reference

Find projects by AWS service for quick navigation:

### Compute & Serverless

| Service | Projects |
|---------|----------|
| **Lambda** | [serverless-api](./serverless-api), [document-processing](./document-processing), [multi-tenant-saas](./multi-tenant-saas), [fleet-tracking](./fleet-tracking), [messaging-platform](./messaging-platform), [banking-transactions](./banking-transactions), [call-center-analytics](./call-center-analytics), [conversational-ai](./conversational-ai), [data-lake-analytics](./data-lake-analytics), [emr-fraud-detection](./emr-fraud-detection), [genai-knowledge-assistant](./genai-knowledge-assistant), [healthcare-imaging-lake](./healthcare-imaging-lake), [secure-ml-transformation](./secure-ml-transformation), [ml-canary-deployment](./ml-canary-deployment) |
| **EMR (Spark)** | [emr-fraud-detection](./emr-fraud-detection) |
| **Elastic Beanstalk** | [hybrid-enterprise-app](./hybrid-enterprise-app) |
| **EC2 Auto Scaling** | [banking-transactions](./banking-transactions) |
| **Step Functions** | [serverless-api](./serverless-api), [document-processing](./document-processing), [emr-fraud-detection](./emr-fraud-detection) |

### Messaging & Streaming

| Service | Projects |
|---------|----------|
| **SQS** | [serverless-api](./serverless-api), [banking-transactions](./banking-transactions) |
| **SNS** | [serverless-api](./serverless-api), [fleet-tracking](./fleet-tracking), [messaging-platform](./messaging-platform), [emr-fraud-detection](./emr-fraud-detection), [ml-canary-deployment](./ml-canary-deployment) |
| **Kinesis Data Streams** | [fleet-tracking](./fleet-tracking), [messaging-platform](./messaging-platform), [emr-fraud-detection](./emr-fraud-detection) |
| **EventBridge** | [serverless-api](./serverless-api), [fleet-tracking](./fleet-tracking), [secure-ml-transformation](./secure-ml-transformation), [ml-canary-deployment](./ml-canary-deployment) |
| **Pinpoint** | [messaging-platform](./messaging-platform) |

### Databases & Storage

| Service | Projects |
|---------|----------|
| **DynamoDB** | [serverless-api](./serverless-api), [fleet-tracking](./fleet-tracking), [messaging-platform](./messaging-platform), [banking-transactions](./banking-transactions), [conversational-ai](./conversational-ai), [emr-fraud-detection](./emr-fraud-detection), [genai-knowledge-assistant](./genai-knowledge-assistant), [ml-canary-deployment](./ml-canary-deployment) |
| **S3** | [document-processing](./document-processing), [fleet-tracking](./fleet-tracking), [messaging-platform](./messaging-platform), [call-center-analytics](./call-center-analytics), [data-lake-analytics](./data-lake-analytics), [hybrid-enterprise-app](./hybrid-enterprise-app), [emr-fraud-detection](./emr-fraud-detection), [genai-knowledge-assistant](./genai-knowledge-assistant), [healthcare-imaging-lake](./healthcare-imaging-lake), [secure-ml-transformation](./secure-ml-transformation), [ml-canary-deployment](./ml-canary-deployment) |
| **OpenSearch** | [call-center-analytics](./call-center-analytics), [genai-knowledge-assistant](./genai-knowledge-assistant) |

### AI/ML Services

| Service | Projects |
|---------|----------|
| **Bedrock (Claude)** | [document-processing](./document-processing), [multi-tenant-saas](./multi-tenant-saas), [genai-knowledge-assistant](./genai-knowledge-assistant) |
| **Bedrock Knowledge Bases** | [genai-knowledge-assistant](./genai-knowledge-assistant) |
| **Bedrock Agents** | [genai-knowledge-assistant](./genai-knowledge-assistant) |
| **Bedrock Titan Embeddings** | [genai-knowledge-assistant](./genai-knowledge-assistant) |
| **Comprehend** | [document-processing](./document-processing), [call-center-analytics](./call-center-analytics) |
| **Lex V2** | [conversational-ai](./conversational-ai) |
| **SageMaker** | [document-processing](./document-processing), [ml-canary-deployment](./ml-canary-deployment) |
| **Textract** | [document-processing](./document-processing) |
| **Rekognition** | [document-processing](./document-processing) |
| **Transcribe** | [document-processing](./document-processing) |

### Analytics & Data Lake

| Service | Projects |
|---------|----------|
| **EMR (Spark MLlib)** | [emr-fraud-detection](./emr-fraud-detection) |
| **Athena** | [data-lake-analytics](./data-lake-analytics), [healthcare-imaging-lake](./healthcare-imaging-lake) |
| **Glue ETL** | [data-lake-analytics](./data-lake-analytics), [healthcare-imaging-lake](./healthcare-imaging-lake), [secure-ml-transformation](./secure-ml-transformation) |
| **Glue DataBrew** | [secure-ml-transformation](./secure-ml-transformation) |
| **Lake Formation** | [data-lake-analytics](./data-lake-analytics), [healthcare-imaging-lake](./healthcare-imaging-lake) |

### Security & Identity

| Service | Projects |
|---------|----------|
| **Cognito** | [multi-tenant-saas](./multi-tenant-saas) |
| **WAF** | [multi-tenant-saas](./multi-tenant-saas) |
| **KMS** | [multi-tenant-saas](./multi-tenant-saas), [healthcare-imaging-lake](./healthcare-imaging-lake), [secure-ml-transformation](./secure-ml-transformation) |
| **Secrets Manager** | [multi-tenant-saas](./multi-tenant-saas) |
| **CloudTrail** | [multi-tenant-saas](./multi-tenant-saas) |

### Networking & Hybrid

| Service | Projects |
|---------|----------|
| **API Gateway** | [banking-transactions](./banking-transactions), [call-center-analytics](./call-center-analytics), [conversational-ai](./conversational-ai), [emr-fraud-detection](./emr-fraud-detection), [genai-knowledge-assistant](./genai-knowledge-assistant), [ml-canary-deployment](./ml-canary-deployment) |
| **VPC** | [multi-tenant-saas](./multi-tenant-saas), [emr-fraud-detection](./emr-fraud-detection), [secure-ml-transformation](./secure-ml-transformation) |
| **VPN Gateway** | [hybrid-enterprise-app](./hybrid-enterprise-app) |

---

## Architecture Decision Library

A comprehensive knowledge library for making informed AWS architectural decisions. Contains decision trees, trade-off matrices, and elimination rules for choosing the right AWS services.

| Category | Key Decisions |
|----------|---------------|
| [Storage](./aws-architecture-decisions/diagrams/storage-decisions.md) | S3 vs EFS vs EBS, FSx family, lifecycle policies |
| [Compute](./aws-architecture-decisions/diagrams/compute-decisions.md) | Lambda vs Fargate vs EC2, Spot vs Reserved, tenancy |
| [Database](./aws-architecture-decisions/diagrams/database-decisions.md) | DynamoDB vs RDS vs Aurora, Multi-AZ vs Read Replicas |
| [Messaging](./aws-architecture-decisions/diagrams/messaging-decisions.md) | SQS vs SNS vs Kinesis, FIFO ordering |
| [Networking](./aws-architecture-decisions/diagrams/networking-decisions.md) | ALB vs NLB, CloudFront vs Global Accelerator, VPC Endpoints |
| [Security](./aws-architecture-decisions/diagrams/security-decisions.md) | IAM, SCPs, encryption options, threat detection |
| [Caching](./aws-architecture-decisions/diagrams/caching-decisions.md) | DAX vs ElastiCache vs CloudFront |
| [Scaling](./aws-architecture-decisions/diagrams/scaling-decisions.md) | Auto Scaling policies, placement groups |
| [Migration](./aws-architecture-decisions/diagrams/migration-decisions.md) | DMS, SCT, Snowball, hybrid connectivity |
| [Analytics](./aws-architecture-decisions/diagrams/analytics-decisions.md) | Athena vs Redshift vs EMR, data lakes |
| [Containers](./aws-architecture-decisions/diagrams/containers-decisions.md) | ECS vs EKS, Fargate, IRSA |
| [High Availability](./aws-architecture-decisions/diagrams/high-availability-decisions.md) | DR patterns, Multi-AZ, Aurora Global |
| [AI & ML](./aws-architecture-decisions/diagrams/ai-ml-decisions.md) | Comprehend, Textract, Rekognition, Bedrock |

[View full decision library →](./aws-architecture-decisions/README.md)

---

## serverless-api

**Task Automation System** - A serverless task processing pipeline demonstrating core Lambda patterns.

### Architecture Highlights
- **EventBridge** scheduled task generation
- **SQS** queue processing with partial batch failure handling
- **Step Functions** workflow orchestration with retry/catch
- **DynamoDB** state persistence
- **SNS** notifications

### Tech Stack
- Java 21 with SnapStart for fast cold starts
- AWS SDK v2 with optimized HTTP client
- AWS Lambda Powertools (tracing, logging, idempotency)
- Terraform modular infrastructure

### Quick Start
```bash
cd serverless-api
./scripts/build.sh
./scripts/deploy.sh
```

[View full documentation](./serverless-api/README.md) | [Business Logic](./serverless-api/docs/BUSINESS_LOGIC.md)

---

## document-processing

**Intelligent Document Processing Platform** - A full ML pipeline demonstrating AWS AI/ML services.

### Architecture Highlights
- **Document Ingestion** via S3 triggers
- **Text Extraction** with Textract (PDFs, images)
- **Audio Transcription** with Transcribe
- **Content Analysis** with Comprehend (NLP) and Rekognition (vision)
- **Document Classification** with SageMaker custom models
- **Summarization & Q&A** with Bedrock (Claude)
- **Workflow Orchestration** with Step Functions

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation
- AWS Lambda Powertools
- XGBoost for document classification
- Claude 3 Sonnet for generative AI
- Terraform modular infrastructure

### Quick Start
```bash
cd document-processing
./scripts/build.sh
./scripts/deploy.sh
```

[View full documentation](./document-processing/README.md) | [Business Logic](./document-processing/docs/BUSINESS_LOGIC.md)

---

## multi-tenant-saas

**Multi-Tenant SaaS Platform for intelliswarm.ai** - GenAI-powered email and CRM intelligence solution for enterprises of 50-10,000 employees.

### Use Case
- **Email Intelligence** - Connect Microsoft 365/Google Workspace mailboxes and analyze emails using GenAI (Amazon Bedrock/Claude)
- **CRM Integration** - Sync contacts, deals, and activities with Salesforce, HubSpot, or Dynamics 365
- **Smart Prioritization** - AI-powered email sentiment analysis, intent detection, and priority scoring
- **Action Extraction** - Automatically extract action items and tasks from email conversations

### Architecture Highlights
- **Cognito Authentication** with MFA, custom Lambda authorizer
- **VPC Integration** for private Lambda deployment with VPC Endpoints
- **WAF Protection** with rate limiting, SQL injection, and XSS prevention
- **KMS Encryption** for all data at rest
- **Secrets Manager** with automatic rotation for OAuth tokens
- **CloudTrail** multi-region audit logging with Insights
- **AWS Config** compliance monitoring with managed rules
- **Budgets** cost management with anomaly detection
- **Multi-Tenant** architecture with Cognito claims-based isolation

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation and settings
- JWT validation with python-jose
- AWS Lambda Powertools (logging, tracing, metrics)
- Amazon Bedrock (Claude 3 Sonnet) for GenAI
- Terraform modular infrastructure (20+ modules)

### Key Enterprise Features
- **IAM Permission Boundaries** - Prevent privilege escalation
- **VPC Endpoints** - Private AWS service access (S3, DynamoDB, Secrets Manager, Bedrock)
- **Multi-Environment** - Dev/staging/prod with security profiles
- **Cost Management** - Service-specific budgets with alerts

### Quick Start
```bash
cd multi-tenant-saas
./scripts/build.sh
./scripts/deploy.sh --env dev
```

[View full documentation](./multi-tenant-saas/README.md) | [Business Logic](./multi-tenant-saas/docs/BUSINESS_LOGIC.md)

---

## fleet-tracking

**Real-Time GPS Tracking System** - A streaming data platform for delivery truck GPS tracking with multiple consumers.

### Use Case
A company tracking GPS coordinates from delivery trucks in real-time. Coordinates are transmitted every 5 seconds, processed by multiple consumers, and aggregated for reporting.

### Architecture Highlights
- **Kinesis Data Streams** for high-throughput, real-time data ingestion
- **Multiple Consumers** processing the same stream:
  - Dashboard Consumer - Updates DynamoDB with latest truck positions
  - Geofence Consumer - Detects boundary crossings, publishes SNS alerts
  - Archive Consumer - Stores historical data in S3 for analytics
- **EventBridge** scheduled GPS producer (simulator)
- **DynamoDB** for current positions and geofence definitions
- **S3** with lifecycle policies for historical data archival

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation
- AWS Lambda Powertools (logging, tracing, metrics)
- Haversine formula for distance/geofence calculations
- Terraform modular infrastructure (7 modules)

### Key Features
- **Partition Key Design** - truck_id ensures ordered processing per truck
- **Fan-Out Pattern** - Multiple Lambda consumers from single stream
- **Geofence Detection** - Circle/polygon boundary detection with enter/exit alerts
- **Data Aggregation** - Per-truck statistics (distance, speed, idle time)
- **S3 Lifecycle** - Automatic tiering to IA/Glacier for cost optimization

### Quick Start
```bash
cd fleet-tracking
./scripts/build.sh
./scripts/deploy.sh
```

[View full documentation](./fleet-tracking/README.md) | [Business Logic](./fleet-tracking/docs/BUSINESS_LOGIC.md)

---

## messaging-platform

**SMS Marketing Campaign Platform** - A two-way SMS marketing system with subscriber response processing and analytics.

### Use Case
A mobile app sending one-time confirmation messages and multi-engagement marketing campaigns. Subscribers can reply (YES/NO/STOP), and all responses are retained for 1 year for analysis and compliance.

### Architecture Highlights
- **Amazon Pinpoint** SMS channel with journey orchestration
- **Two-Way SMS** subscriber response handling (opt-in, opt-out, confirmations)
- **Kinesis Data Streams** with 365-day retention for compliance
- **Multi-Consumer Processing** - Response handler, analytics, archival
- **DynamoDB** subscriber management with TTL for 1-year retention
- **S3** archival with lifecycle policies (IA → Glacier)
- **SNS** notifications for opt-out alerts

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation
- AWS Lambda Powertools (logging, tracing, metrics)
- Sentiment analysis for response categorization
- Terraform modular infrastructure (8 modules)

### Key Features
- **Keyword Detection** - STOP, UNSUBSCRIBE for opt-out; YES, CONFIRM for opt-in
- **Response Sentiment** - Positive, negative, neutral classification
- **Subscriber Lifecycle** - PENDING → ACTIVE → OPTED_OUT state machine
- **Analytics Aggregation** - Delivery rates, response rates, cost tracking
- **Compliance** - 365-day data retention, opt-out handling

### Quick Start
```bash
cd messaging-platform
./scripts/build.sh
./scripts/deploy.sh
```

[View full documentation](./messaging-platform/README.md) | [Business Logic](./messaging-platform/docs/BUSINESS_LOGIC.md)

---

## banking-transactions

**Online Banking Platform with EC2 Auto Scaling** - A distributed system architecture using SQS-based scaling for transaction processing.

### Use Case
A commercial bank's next-generation online banking platform with highly variable transaction volumes. The system automatically scales EC2 instances based on SQS queue depth.

### Architecture Highlights
- **Amazon SQS** as transaction message buffer with DLQ
- **EC2 Auto Scaling Group** with SQS-based scaling policy
- **Target Tracking Scaling** on custom BacklogPerInstance metric
- **API Gateway + Lambda** for transaction ingestion
- **DynamoDB** for transaction storage and idempotency
- **CloudWatch** custom metrics and dashboards

### Tech Stack
- Python 3.12 with type hints
- Flask + Gunicorn for EC2 application
- Pydantic for data validation
- AWS Lambda Powertools (logging, tracing, metrics)
- Terraform modular infrastructure (6 modules)

### Key Features
- **SQS-Based Scaling** - Scale out/in based on queue depth per instance
- **Idempotency** - Duplicate transaction detection with DynamoDB
- **Dead Letter Queue** - Failed message handling and investigation
- **Multi-threaded Workers** - 4 worker threads per EC2 instance
- **Health Checks** - ALB health checks for instance replacement

### Quick Start
```bash
cd banking-transactions
./scripts/build.sh
./scripts/deploy.sh -e dev
```

[View full documentation](./banking-transactions/README.md) | [Business Logic](./banking-transactions/docs/BUSINESS_LOGIC.md)

---

## call-center-analytics

**Call Center Sentiment Analysis Platform** - Analyze customer service call transcripts using Amazon Comprehend with OpenSearch visualization.

### Use Case
A company analyzing customer service calls to identify satisfaction trends, monitor agent performance, detect escalation patterns, and generate actionable insights for training.

### Architecture Highlights
- **S3 Trigger** automatic processing when transcripts uploaded
- **Amazon Comprehend** sentiment analysis, entity extraction, key phrases
- **Batch Processing** scheduled batch jobs for high volume
- **Amazon OpenSearch** full-text search and analytics dashboards
- **REST API** query calls, stats, agent metrics
- **Speaker Analysis** separate customer vs agent sentiment

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation
- AWS Lambda Powertools (logging, tracing, metrics)
- OpenSearch-py for indexing and queries
- Terraform modular infrastructure (7 modules)

### Key Features
- **Real-time Analysis** immediate processing via S3 events
- **Batch Jobs** scheduled Comprehend batch processing
- **Entity Extraction** identify products, people, organizations
- **Quality Scoring** calculated call quality scores
- **Agent Metrics** performance tracking per agent
- **Trend Analysis** sentiment trends over time

### Quick Start
```bash
cd call-center-analytics
./scripts/build.sh
./scripts/deploy.sh -e dev
```

[View full documentation](./call-center-analytics/README.md) | [Business Logic](./call-center-analytics/docs/BUSINESS_LOGIC.md)

---

## conversational-ai

**Airline Chatbot Platform** - A conversational AI chatbot for flight bookings, booking updates, and check-ins using Amazon Lex.

### Use Case
An airline company wants to reduce call center volume by automating common requests through a 24/7 self-service chatbot accessible via web, mobile, and messaging platforms.

### Architecture Highlights
- **Amazon Lex V2** conversational AI with NLU
- **Three Intents** - BookFlight, UpdateBooking, CheckIn
- **Lambda Fulfillment** dialog validation and business logic
- **DynamoDB** bookings, flights, and check-ins storage
- **Multi-Channel** web widget, mobile app, Slack, Facebook
- **Session Management** conversation context preservation

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation
- AWS Lambda Powertools (logging, tracing, metrics)
- Terraform modular infrastructure (6 modules)

### Key Features
- **Slot Validation** real-time input validation during dialog
- **Flight Search** search and select from available flights
- **Booking Management** create, update, cancel reservations
- **Online Check-In** 24-hour window check-in with seat selection
- **Fallback Handling** graceful handling of unrecognized inputs

### Quick Start
```bash
cd conversational-ai
./scripts/build.sh
./scripts/deploy.sh -e dev
```

[View full documentation](./conversational-ai/README.md) | [Business Logic](./conversational-ai/docs/BUSINESS_LOGIC.md)

---

## data-lake-analytics

**Data Lake Analytics Platform** - A serverless data lake with AWS Glue ETL, Lake Formation security, and Amazon Athena for high-performance analytics.

### Use Case
An application loading hundreds of JSON documents into Amazon S3 every hour. The data is transformed to Apache Parquet format with Snappy compression for optimal query performance, with AWS Lake Formation providing fine-grained access control.

### Architecture Highlights
- **JSON to Parquet** transformation via AWS Glue ETL
- **AWS Lake Formation** for fine-grained data governance
- **Amazon Athena** for serverless SQL analytics
- **Time-based partitioning** (year/month/day/hour)
- **Snappy compression** for 6x storage reduction
- **Predicate pushdown** for efficient column-based queries

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation
- AWS Lambda Powertools (logging, tracing, metrics)
- PySpark for Glue ETL jobs
- Terraform modular infrastructure (8 modules)
- CloudFormation nested stacks

### Key Features
- **Columnar Storage** - 2x faster queries vs row-based formats
- **Partition Projection** - No MSCK REPAIR TABLE needed
- **Lake Formation Security** - lakeformation:GetDataAccess permission model
- **Cost Controls** - BytesScannedCutoff per query
- **Lambda Function URLs** - Direct HTTPS endpoints without API Gateway

### Quick Start
```bash
cd data-lake-analytics
./scripts/build.sh
./scripts/deploy.sh
```

[View full documentation](./data-lake-analytics/README.md) | [Business Logic](./data-lake-analytics/docs/BUSINESS_LOGIC.md)

---

## hybrid-enterprise-app

**Hybrid Enterprise Inventory System** - A migrated full-stack Java application running on AWS Elastic Beanstalk with hybrid connectivity to an on-premises Oracle database.

### Use Case
A company migrating their legacy on-premises inventory management system to AWS. Due to compliance requirements and existing Oracle investments, the database remains on-premises while the application layer moves to AWS, connected via VPN/Direct Connect.

### Architecture Highlights
- **Elastic Beanstalk** managed Java platform with auto-scaling
- **VPN Gateway** secure connectivity to on-premises Oracle database
- **Hybrid Architecture** application in AWS, database on-premises
- **JasperReports** enterprise PDF/Excel report generation
- **S3** report storage with lifecycle policies
- **CloudWatch** monitoring, dashboards, and alarms

### Tech Stack
- Java 21 with Spring Boot 3.2
- Hibernate 6.x with Oracle dialect
- JasperReports 6.21 for reporting
- Thymeleaf for server-side templating
- Spring Security for authentication
- Terraform modular infrastructure (5 modules)

### Key Features
- **On-Premises Oracle** - No database migration required
- **VPN/Direct Connect** - Secure hybrid connectivity
- **Role-Based Access** - Admin, Manager, Staff roles
- **Report Generation** - Inventory and low-stock PDF/Excel reports
- **Multi-Cloud Ready** - Documentation for Azure/GCP equivalents

### Quick Start
```bash
cd hybrid-enterprise-app
./scripts/build.sh
./scripts/deploy.sh -e dev
```

[View full documentation](./hybrid-enterprise-app/README.md) | [Business Logic](./hybrid-enterprise-app/docs/BUSINESS_LOGIC.md)

---

## emr-fraud-detection

**ML Fraud Detection with Spark** - An ML-based fraud detection system processing millions of financial transactions using Amazon EMR with Apache Spark.

### Use Case
A financial institution detecting fraudulent transactions in near real-time. Transactions are ingested via API, features are engineered at scale using Spark, and ML models score each transaction for fraud probability with alerts for investigation.

### Architecture Highlights
- **Kinesis Data Streams** real-time transaction ingestion
- **EMR Spark** transient clusters for batch processing (cost-optimized)
- **Spark MLlib** Random Forest classifier for fraud detection
- **Spark Structured Streaming** near real-time scoring from Kinesis
- **Step Functions** ML pipeline orchestration (feature engineering → training → scoring)
- **S3 Data Lake** raw, features, models, predictions zones
- **DynamoDB** fraud alerts and prediction results
- **SNS** real-time fraud notifications

### Tech Stack
- Python 3.12 with type hints
- PySpark for feature engineering and ML
- Spark MLlib (Random Forest, 100 trees)
- Pydantic for data validation
- AWS Lambda Powertools (logging, tracing, metrics)
- Terraform modular infrastructure (11 modules)
- CloudFormation nested stacks (11 templates)

### Key Features
- **Feature Engineering** - Velocity, behavioral, distance, temporal features
- **Dual Scoring Modes** - Batch (Step Functions) and streaming (Structured Streaming)
- **Transient EMR** - Clusters created per pipeline run, auto-terminate after
- **Spot Instances** - 50-70% cost savings on task nodes
- **Risk Factor Identification** - HIGH_AMOUNT, HIGH_VELOCITY, NEW_MERCHANT, IMPOSSIBLE_TRAVEL
- **Fraud Thresholds** - 0.7+ (fraudulent), 0.4-0.7 (suspicious)

### Quick Start
```bash
cd emr-fraud-detection
./scripts/build.sh --all
./scripts/deploy.sh -e dev
```

[View full documentation](./emr-fraud-detection/README.md) | [Business Logic](./emr-fraud-detection/docs/BUSINESS_LOGIC.md)

---

## genai-knowledge-assistant

**RAG-Powered Enterprise Knowledge Assistant** - An intelligent Q&A system using Amazon Bedrock Knowledge Bases and Agents for retrieval-augmented generation over enterprise documents.

### Use Case
Enterprises building intelligent assistants to answer questions based on internal documentation, policies, and knowledge bases. The system provides grounded, accurate answers with source citations using RAG (Retrieval-Augmented Generation).

### Architecture Highlights
- **Amazon Bedrock Knowledge Bases** managed document ingestion and semantic search
- **Amazon Bedrock Agents** autonomous agents with multi-turn conversations
- **OpenSearch Serverless** vector store for embedding storage and retrieval
- **RAG Pipeline** query embedding → vector search → context assembly → LLM generation
- **Document Processing** automatic chunking, embedding, and indexing
- **Citation Support** responses include source attribution

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation
- AWS Lambda Powertools (logging, tracing, metrics)
- Claude 3.5 Sonnet for response generation
- Titan Embeddings V2 for 1024-dimension vectors
- Terraform modular infrastructure (8 modules)
- CloudFormation nested stacks (8 templates)
- SAM template for rapid deployment

### Key Features
- **Semantic Search** vector similarity search with configurable top-k
- **Hybrid Retrieval** combine semantic and keyword search
- **Bedrock Agents** autonomous reasoning with tool use
- **Session Memory** multi-turn conversation context
- **Document Sync** scheduled and on-demand knowledge base sync
- **Guardrails** content filtering and safety controls

### Quick Start
```bash
cd genai-knowledge-assistant
./scripts/build.sh
./scripts/deploy.sh -e dev
```

[View full documentation](./genai-knowledge-assistant/README.md) | [Business Logic](./genai-knowledge-assistant/docs/BUSINESS_LOGIC.md)

---

## healthcare-imaging-lake

**HIPAA-Compliant Healthcare Imaging Data Lake** - A secure data lake for organizing 10M+ patient medical images and clinical records for ML model training, with fine-grained access control.

### Use Case
A healthcare ML team needs to organize patient medical imaging data (CT scans, MRIs, X-rays) along with clinical records. The system must be HIPAA-compliant, support multi-modal queries across images and structured data, and enable subset extraction for specific medical conditions (e.g., "all chest X-rays with pneumonia diagnosis").

### Architecture Highlights
- **S3 with SSE-KMS** encrypted storage for images and metadata
- **AWS Glue Data Catalog** unified metadata management with crawlers
- **Lake Formation** fine-grained access control (row-level, cell-level, column-level)
- **Amazon Athena** SQL queries with partition projection
- **Data Cell Filters** PHI masking for researcher access
- **Multi-modal Queries** join imaging and clinical data

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation
- AWS Lambda Powertools (logging, tracing, metrics)
- PySpark for Glue ETL jobs
- Terraform modular infrastructure (8 modules)
- CloudFormation nested stacks (8 templates)
- SAM template for rapid deployment

### Key Features
- **HIPAA Compliance** - Customer-managed KMS keys with rotation, audit logging
- **Partition Projection** - No MSCK REPAIR TABLE needed for time-based partitions
- **Data Cell Filters** - Exclude PHI columns (patient_id, physician_id) for researchers
- **ML Cohort Extraction** - Named queries for extracting training datasets by condition codes
- **DICOM Metadata** - Store and query DICOM tags alongside clinical data

### Quick Start
```bash
cd healthcare-imaging-lake
./scripts/build.sh
./scripts/deploy.sh -e dev
```

[View full documentation](./healthcare-imaging-lake/README.md) | [Business Logic](./healthcare-imaging-lake/docs/BUSINESS_LOGIC.md)

---

## secure-ml-transformation

**Secure ML Data Transformation Pipeline** - A VPC-isolated data transformation pipeline for financial ML fraud detection using AWS Glue, DataBrew, and custom PySpark transformations.

### Use Case
A financial institution must transform sensitive transaction data for ML fraud detection models. The solution maintains strict data lineage, supports audit trails, and processes data within a VPC without internet access.

### Architecture Highlights
- **VPC Isolation** - No internet gateway, private subnets only
- **VPC Endpoints** - S3, Glue, CloudWatch, KMS, Secrets Manager
- **AWS Glue ETL** - Custom PySpark transformations
- **Glue DataBrew** - Sensitive data detection and profiling
- **Glue Job Bookmarks** - Data lineage tracking
- **KMS Encryption** - Customer-managed keys for all data
- **CloudWatch Logs** - Encrypted audit trails

### Tech Stack
- Python 3.12 with type hints
- PySpark for Glue ETL jobs
- Pydantic for data validation
- AWS Lambda Powertools (logging, tracing, metrics)
- Isolation Forest for anomaly detection
- Terraform modular infrastructure (6 modules)
- CloudFormation nested stacks (6 templates)

### Key Features
- **PII Tokenization** - Deterministic, format-preserving, and hash methods
- **Transaction Binning** - Percentile, quantile, and custom ranges
- **Merchant Encoding** - Hierarchical category mapping with risk scoring
- **Anomaly Detection** - Isolation Forest with temporal/velocity features
- **Data Lineage** - Job bookmarks and catalog metadata

### Quick Start
```bash
cd secure-ml-transformation
./scripts/build.sh
./scripts/deploy.sh -e dev
```

[View full documentation](./secure-ml-transformation/README.md) | [Business Logic](./secure-ml-transformation/docs/BUSINESS_LOGIC.md)

---

## ml-canary-deployment

**ML Canary Deployment with Traffic Splitting** - A production-ready solution for deploying ML models with canary releases, traffic splitting, and A/B testing on Amazon SageMaker.

### Use Case
A media streaming company serving millions of daily active users needs to safely deploy new ML recommendation models with sub-100ms inference latency. The system gradually shifts traffic to new model versions while monitoring for regressions.

### Architecture Highlights
- **SageMaker Production Variants** - Multiple model versions on single endpoint
- **Traffic Splitting** - Gradual traffic shifting via UpdateEndpointWeightsAndCapacities
- **Auto-Rollback** - Automatic rollback when latency or error rate thresholds exceeded
- **Auto-Scaling** - Scale instances based on invocations per instance
- **Real-time Monitoring** - CloudWatch metrics, alarms, and dashboards
- **SNS Alerts** - Notifications for deployment events

### Tech Stack
- Python 3.12 with type hints
- Pydantic for data validation
- AWS Lambda Powertools (logging, tracing, metrics)
- XGBoost for model training
- Terraform modular infrastructure (7 modules)
- CloudFormation nested stacks (7 templates)
- SAM template for local development

### Key Features
- **Canary Deployments** - Start at 10% traffic, gradually increase
- **A/B Testing** - Compare model performance with built-in metrics
- **P99 Latency Monitoring** - Sub-100ms latency threshold enforcement
- **Error Rate Tracking** - Automatic rollback at 1% error rate
- **Zero-Downtime Updates** - Traffic shifts without endpoint recreation

### Quick Start
```bash
cd ml-canary-deployment
./scripts/build.sh
./scripts/deploy.sh -e dev
```

[View full documentation](./ml-canary-deployment/README.md) | [Business Logic](./ml-canary-deployment/docs/BUSINESS_LOGIC.md)

---

## Common Patterns

All projects demonstrate:

### Infrastructure as Code
- **Dual IaC Support** - Both Terraform and CloudFormation for each project
- **Modular Terraform** - Reusable modules for Lambda, SQS, DynamoDB, etc.
- **CloudFormation Nested Stacks** - S3-hosted templates with deploy scripts
- **Environment-based configuration** - Dev, staging, production support
- **Output values** for cross-stack references

### Serverless Best Practices
- **Event-driven architecture** - Loose coupling via events and queues
- **Idempotency** - Safe retries with deduplication
- **Error handling** - DLQs, retry policies, alerting
- **Observability** - CloudWatch logs, metrics, X-Ray tracing

### Security
- **IAM least privilege** - Minimal permissions per function
- **Secrets management** - Secrets Manager / Parameter Store
- **Encryption at rest** - KMS customer managed keys
- **VPC isolation** - Optional private subnet deployment

---

## Prerequisites

### Common Requirements
- **AWS CLI** configured with appropriate credentials
- **Terraform 1.5+** (for Terraform deployments)
- **AWS CloudFormation** (for CloudFormation deployments)
- **S3 Bucket** for CloudFormation nested stack templates
- **AWS Account** with admin or sufficient permissions

### serverless-api / hybrid-enterprise-app (Java)
- Java 21 (Amazon Corretto recommended)
- Maven 3.9+

### document-processing / multi-tenant-saas / fleet-tracking / messaging-platform / banking-transactions / call-center-analytics / conversational-ai / data-lake-analytics / emr-fraud-detection / genai-knowledge-assistant / healthcare-imaging-lake / secure-ml-transformation / ml-canary-deployment (Python)
- Python 3.12+
- pip or uv for package management

---

## Deployment Options

Each project supports two Infrastructure as Code approaches:

### Option 1: Terraform
```bash
cd <project>/terraform
terraform init
terraform plan
terraform apply
```

### Option 2: CloudFormation
```bash
cd <project>
./scripts/deploy-cfn.sh --env dev --bucket your-cfn-bucket
```

The CloudFormation deploy script:
1. Syncs nested templates to S3
2. Replaces local paths with S3 URLs
3. Creates/updates the CloudFormation stack

---

## AWS Region

All projects default to **eu-central-2** (EU Zurich). Configure via:

**Terraform** - Modify `terraform.tfvars`:
```hcl
aws_region = "eu-central-2"  # EU Zurich
```

**CloudFormation** - Use `--region` flag or set `AWS_DEFAULT_REGION`

---

## Cost Considerations

Most projects use serverless, pay-per-use services. The hybrid-enterprise-app project uses EC2-based pricing:

| Service | Free Tier | Pricing |
|---------|-----------|---------|
| Lambda | 1M requests/month | $0.20/1M requests |
| SQS | 1M requests/month | $0.40/1M requests |
| DynamoDB | 25GB storage | On-demand per request |
| Step Functions | 4,000 transitions/month | $25/1M transitions |
| S3 | 5GB storage | $0.023/GB/month |
| Cognito | 50K MAU | $0.0055/MAU after |
| NAT Gateway | None | $0.045/hour + data |
| KMS | None | $1/key/month |
| Kinesis | None | $0.015/shard-hour |
| Pinpoint | 100 SMS/month | $0.00645/SMS (US) |
| Comprehend | None | $0.0001/unit (sentiment) |
| OpenSearch | None | ~$0.036/hour (t3.small) |
| OpenSearch Serverless | None | $0.24/OCU-hour (~$350/mo min) |
| Bedrock Claude 3.5 | None | $3/1M input, $15/1M output tokens |
| Bedrock Titan Embeddings | None | $0.02/1M tokens |
| Lex | None | $0.004/speech, $0.00075/text |
| Athena | None | $5/TB scanned |
| Glue ETL | None | $0.44/DPU-hour |
| Glue DataBrew | None | $1/node-hour |
| Lake Formation | None | No additional charge |
| Elastic Beanstalk | None (EC2 costs) | ~$30/mo per t3.medium |
| EC2 Auto Scaling | None (EC2 costs) | ~$30/mo per t3.medium |
| EMR | None | $0.192/hr (m5.xlarge) + EC2 |
| SageMaker Endpoints | None | $0.126/hr (ml.m5.large) |
| VPN Gateway | None | $0.05/hour (~$36/mo) |
| VPC Endpoints | None | $0.01/hr + $0.01/GB |

**Tip**: Use `./scripts/deploy.sh --destroy` to tear down resources when not in use.

---

## Project Structure

```
aws-prorotypes/
├── README.md                      # This file
├── serverless-api/                # Java Task Automation System
│   ├── lambda/                    # Maven multi-module project
│   ├── terraform/                 # Terraform infrastructure
│   ├── cloudformation/            # CloudFormation nested stacks
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── document-processing/           # Python ML Platform
│   ├── src/                       # Python Lambda source
│   ├── sagemaker/                 # Training code
│   ├── terraform/                 # Terraform infrastructure
│   ├── cloudformation/            # CloudFormation nested stacks
│   ├── tests/                     # Unit and integration tests
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── multi-tenant-saas/             # Enterprise API Platform
│   ├── src/                       # Python Lambda source
│   ├── terraform/                 # Terraform infrastructure (20+ modules)
│   ├── cloudformation/            # CloudFormation nested stacks
│   ├── environments/              # Dev/staging/prod configs
│   ├── policies/                  # IAM policy documents
│   ├── tests/                     # Unit and integration tests
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── fleet-tracking/                # Real-Time GPS Tracking
│   ├── src/                       # Python Lambda source
│   ├── terraform/                 # Terraform infrastructure (7 modules)
│   ├── cloudformation/            # CloudFormation nested stacks
│   ├── tests/                     # Unit and integration tests
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── messaging-platform/            # SMS Marketing Campaign Platform
│   ├── src/                       # Python Lambda source
│   ├── terraform/                 # Terraform infrastructure (8 modules)
│   ├── cloudformation/            # CloudFormation nested stacks
│   ├── tests/                     # Unit and integration tests
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── banking-transactions/          # Online Banking Platform with SQS Auto Scaling
│   ├── src/                       # Python source (Lambda + EC2)
│   ├── terraform/                 # Terraform infrastructure (6 modules)
│   ├── cloudformation/            # CloudFormation nested stacks
│   ├── tests/                     # Unit and integration tests
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── call-center-analytics/         # Call Center Sentiment Analysis
│   ├── src/                       # Python Lambda source
│   ├── terraform/                 # Terraform infrastructure (7 modules)
│   ├── cloudformation/            # CloudFormation nested stacks
│   ├── tests/                     # Unit and integration tests
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── conversational-ai/             # Airline Chatbot Platform
│   ├── src/                       # Python Lambda source
│   ├── terraform/                 # Terraform infrastructure (6 modules)
│   ├── cloudformation/            # CloudFormation nested stacks
│   ├── tests/                     # Unit and integration tests
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── data-lake-analytics/           # Data Lake Analytics Platform
│   ├── src/                       # Python Lambda source
│   ├── glue/                      # PySpark ETL scripts
│   ├── terraform/                 # Terraform infrastructure (8 modules)
│   ├── cloudformation/            # CloudFormation nested stacks
│   ├── tests/                     # Unit and integration tests
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── hybrid-enterprise-app/         # Hybrid Enterprise Inventory
│   ├── application/               # Spring Boot application
│   │   ├── src/                   # Java source (ai.intelliswarm.inventory)
│   │   ├── .ebextensions/         # EB configuration
│   │   └── pom.xml                # Maven configuration
│   ├── terraform/                 # Terraform infrastructure (5 modules)
│   ├── cloudformation/            # CloudFormation nested stacks
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── emr-fraud-detection/           # ML Fraud Detection with Spark
│   ├── src/                       # Python Lambda source
│   ├── spark/                     # PySpark jobs and utilities
│   │   ├── jobs/                  # Feature engineering, training, scoring
│   │   └── utils/                 # Spark session and feature utilities
│   ├── terraform/                 # Terraform infrastructure (11 modules)
│   ├── cloudformation/            # CloudFormation nested stacks
│   ├── tests/                     # Unit and integration tests
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── genai-knowledge-assistant/     # RAG Knowledge Base Assistant
│   ├── src/                       # Python Lambda source
│   │   ├── common/                # Config, models, exceptions, clients
│   │   ├── handlers/              # API, query, ingestion, agent, sync
│   │   └── services/              # Bedrock, embedding, vector store, KB
│   ├── terraform/                 # Terraform infrastructure (8 modules)
│   ├── cloudformation/            # CloudFormation nested stacks (8 templates)
│   ├── sam/                       # SAM template and config
│   ├── tests/                     # Unit and integration tests
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── healthcare-imaging-lake/       # HIPAA-Compliant Healthcare Imaging Data Lake
│   ├── src/                       # Python Lambda source
│   │   ├── common/                # Config, models, exceptions
│   │   ├── handlers/              # API, ingestion, catalog, query
│   │   └── services/              # S3, KMS, Glue, Lake Formation, Athena
│   ├── glue/                      # PySpark ETL scripts
│   ├── terraform/                 # Terraform infrastructure (8 modules)
│   ├── cloudformation/            # CloudFormation nested stacks (8 templates)
│   ├── sam/                       # SAM template and config
│   ├── tests/                     # Unit and integration tests
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
├── secure-ml-transformation/      # Secure ML Data Transformation Pipeline
│   ├── src/                       # Python Lambda source
│   │   ├── common/                # Config, models, exceptions, clients
│   │   ├── handlers/              # Job trigger, lineage, audit
│   │   └── services/              # Glue, DataBrew, lineage, audit
│   ├── glue/                      # PySpark ETL jobs
│   │   └── jobs/                  # Tokenization, binning, encoding, anomaly
│   ├── terraform/                 # Terraform infrastructure (6 modules)
│   ├── cloudformation/            # CloudFormation nested stacks (6 templates)
│   ├── sam/                       # SAM template and config
│   ├── tests/                     # Unit and integration tests
│   ├── docs/                      # Business logic & cost simulation
│   ├── scripts/                   # Build/deploy scripts
│   └── README.md
└── ml-canary-deployment/          # ML Canary Deployment with Traffic Splitting
    ├── src/                       # Python Lambda source
    │   ├── common/                # Config, models, exceptions, clients
    │   ├── handlers/              # API, deployment, monitoring, rollback
    │   └── services/              # Inference, deployment, traffic, monitoring
    ├── sagemaker/                 # SageMaker training code
    │   └── training/              # Train, inference, preprocessing
    ├── terraform/                 # Terraform infrastructure (7 modules)
    ├── cloudformation/            # CloudFormation nested stacks (7 templates)
    ├── sam/                       # SAM template and config
    ├── tests/                     # Unit and integration tests
    ├── docs/                      # Business logic & cost simulation
    ├── scripts/                   # Build/deploy scripts
    └── README.md
```

---

## License

These projects are for educational and demonstration purposes.
