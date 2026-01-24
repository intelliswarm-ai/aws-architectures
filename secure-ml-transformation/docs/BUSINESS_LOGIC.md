# Business Logic Documentation

## Overview

This document describes the business logic for the Secure ML Data Transformation Pipeline, designed for financial institutions requiring PII protection and ML-ready data preparation for fraud detection models.

## Problem Statement

Financial institutions need to:
1. Transform sensitive transaction data for ML model training
2. Protect PII while maintaining analytical utility
3. Process data within strict network boundaries (no internet access)
4. Maintain complete audit trails for regulatory compliance
5. Ensure data lineage for model governance

## Solution Architecture

### Data Flow

```
Raw Transactions --> DataBrew Profile --> PII Detection --> Tokenization
                                                               |
                                                               v
                                          Amount Binning <-- Validated Data
                                                               |
                                                               v
                                      Merchant Encoding <-- Binned Data
                                                               |
                                                               v
                                       Anomaly Flagging <-- Encoded Data
                                                               |
                                                               v
                                        ML-Ready Output --> S3 Output
```

## Data Transformation Logic

### 1. PII Tokenization

#### Purpose
Replace sensitive identifiers with tokens that:
- Cannot be reversed without access to the tokenization key
- Maintain referential integrity across records
- Preserve analytical utility (deterministic tokens enable joins)

#### Implementation

**Deterministic Tokenization (for joinable fields)**
```
token = HMAC-SHA256(value + salt)[:16]
```
- Used for: customer_id, account_number
- Produces consistent tokens for the same input
- Salt is environment-specific and stored in AWS Secrets Manager

**Format-Preserving Tokenization**
```
original: "4532-1234-5678-9012"
tokenized: "4532-XXXX-XXXX-7291"
```
- Used for: card_number (preserves BIN for analysis)
- Maintains field format for downstream validation

**Hash Tokenization (one-way)**
```
token = SHA256(value)
```
- Used for: email, phone (when not needed for joins)
- Irreversible transformation

#### Configuration Schema
```json
{
    "pii_columns": [
        {
            "column_name": "customer_id",
            "method": "deterministic",
            "output_length": 16
        },
        {
            "column_name": "card_number",
            "method": "format_preserving",
            "preserve_prefix": 4,
            "preserve_suffix": 4
        },
        {
            "column_name": "email",
            "method": "hash",
            "algorithm": "sha256"
        }
    ]
}
```

### 2. Transaction Amount Binning

#### Purpose
Convert continuous transaction amounts into categorical bins that:
- Reduce noise and outlier impact on models
- Align with business-meaningful ranges
- Enable consistent feature encoding

#### Binning Methods

**Percentile-Based Binning**
```python
# Bins based on historical distribution
bins = [0, p10, p25, p50, p75, p90, p95, p99, max]
labels = ["micro", "small", "low", "medium", "high", "large", "very_large", "extreme"]
```

**Custom Range Binning**
```python
# Business-defined ranges
bins = [0, 10, 50, 100, 500, 1000, 5000, float('inf')]
labels = ["trivial", "small", "medium", "standard", "large", "significant", "major"]
```

**Quantile Binning**
```python
# Equal-frequency bins
n_bins = 10
bins = pd.qcut(amounts, q=n_bins, labels=False)
```

#### Configuration Schema
```json
{
    "amount_binning": {
        "method": "percentile",
        "column": "transaction_amount",
        "percentiles": [0, 10, 25, 50, 75, 90, 95, 99, 100],
        "labels": ["micro", "small", "low", "medium", "high", "large", "very_large", "extreme"],
        "handle_negatives": "absolute",
        "null_handling": "separate_bin"
    }
}
```

### 3. Merchant Category Encoding

#### Purpose
Transform merchant category codes (MCC) into ML-friendly features:
- Map raw codes to standardized categories
- Include risk indicators
- Handle unknown/new merchant codes

#### Mapping Structure
```json
{
    "merchant_mapping": {
        "5411": {
            "category": "grocery_stores",
            "category_id": 1,
            "risk_level": "low",
            "risk_score": 0.1,
            "parent_category": "retail",
            "is_cash_equivalent": false
        },
        "5812": {
            "category": "eating_places_restaurants",
            "category_id": 2,
            "risk_level": "medium",
            "risk_score": 0.3,
            "parent_category": "dining",
            "is_cash_equivalent": false
        },
        "6011": {
            "category": "atm_cash_disbursements",
            "category_id": 15,
            "risk_level": "high",
            "risk_score": 0.7,
            "parent_category": "financial",
            "is_cash_equivalent": true
        },
        "_default": {
            "category": "unknown",
            "category_id": 999,
            "risk_level": "high",
            "risk_score": 0.8,
            "parent_category": "uncategorized",
            "is_cash_equivalent": false
        }
    }
}
```

#### Output Features
- `merchant_category`: Encoded category name
- `merchant_category_id`: Numeric encoding for embedding
- `merchant_risk_level`: Categorical risk indicator
- `merchant_risk_score`: Numeric risk score [0, 1]
- `merchant_parent_category`: Hierarchical grouping
- `is_cash_equivalent`: Boolean flag for high-risk transaction types

### 4. Anomaly Detection (Isolation Forest)

#### Purpose
Flag transactions that deviate from normal patterns:
- Pre-label data for model training
- Enable semi-supervised learning
- Provide baseline fraud indicators

#### Features Used
```python
anomaly_features = [
    "amount_bin_encoded",      # Binned amount (numeric)
    "merchant_risk_score",     # Risk score from mapping
    "hour_of_day",             # Temporal feature
    "day_of_week",             # Temporal feature
    "transaction_velocity",    # Transactions per hour for customer
    "amount_deviation",        # Deviation from customer mean
    "merchant_diversity",      # Unique merchants in window
    "geographic_distance"      # Distance from last transaction
]
```

#### Isolation Forest Parameters
```python
isolation_forest_config = {
    "n_estimators": 100,           # Number of trees
    "contamination": 0.01,         # Expected anomaly ratio
    "max_samples": "auto",         # Samples per tree
    "max_features": 1.0,           # Features per tree
    "bootstrap": False,            # Sampling without replacement
    "random_state": 42             # Reproducibility
}
```

#### Output
- `anomaly_score`: Raw isolation score [-1, 1]
- `is_anomaly`: Boolean flag (True if score < threshold)
- `anomaly_percentile`: Percentile rank of anomaly score

## Data Lineage

### Glue Job Bookmarks

Job bookmarks track:
- Last processed timestamp/partition
- Input/output record counts
- Transformation parameters used
- Execution duration and status

### Lineage Metadata Schema
```json
{
    "job_execution_id": "jr_abc123",
    "job_name": "secure-ml-transform-main-etl",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T10:15:00Z",
    "input_records": 1000000,
    "output_records": 999500,
    "filtered_records": 500,
    "transformations_applied": [
        "pii_tokenization",
        "amount_binning",
        "merchant_encoding",
        "anomaly_detection"
    ],
    "input_paths": ["s3://raw-bucket/transactions/2024/01/15/"],
    "output_paths": ["s3://processed-bucket/ml-ready/2024/01/15/"],
    "parameters": {
        "binning_method": "percentile",
        "contamination": 0.01
    }
}
```

## Audit Trail

### Logged Events
1. **Job Start**: Parameters, input sources, user/role
2. **Data Access**: S3 reads/writes with paths and sizes
3. **Transformation Steps**: Each transformation with timing
4. **Sensitive Data Detection**: DataBrew findings
5. **Errors**: Full stack traces and context
6. **Job Completion**: Summary statistics

### Log Format
```json
{
    "timestamp": "2024-01-15T10:05:23.456Z",
    "event_type": "TRANSFORMATION_COMPLETE",
    "job_execution_id": "jr_abc123",
    "transformation": "pii_tokenization",
    "records_processed": 1000000,
    "records_tokenized": 850000,
    "duration_seconds": 45.2,
    "columns_tokenized": ["customer_id", "card_number", "email"]
}
```

## Error Handling

### Retry Logic
- Transient errors: 3 retries with exponential backoff
- S3 throttling: Automatic retry with jitter
- Glue service errors: Job-level retry (configurable)

### Data Quality Errors
- Missing required fields: Record filtered, logged to DLQ
- Invalid data types: Type coercion attempted, fallback to null
- Out-of-range values: Clamped to valid range, flagged

### Failure Modes
1. **Partial Failure**: Job bookmarks enable resume from checkpoint
2. **Complete Failure**: Alert triggered, no data committed
3. **Data Quality Breach**: Job halted if error rate > 1%

## Performance Considerations

### Partitioning Strategy
- Input: Partitioned by date (year/month/day)
- Output: Partitioned by date + processing_batch_id
- Enables incremental processing and efficient queries

### Resource Sizing
- Standard workload: 10 DPUs
- Large batches (>10M records): 20 DPUs
- Auto-scaling enabled for variable workloads

### Optimization Techniques
- Broadcast joins for small dimension tables (merchant mapping)
- Column pruning to reduce I/O
- Predicate pushdown to S3
- Coalesce output files for optimal read performance
