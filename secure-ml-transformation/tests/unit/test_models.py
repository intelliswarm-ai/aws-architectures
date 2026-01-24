"""Unit tests for Pydantic models."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.common.models import (
    AnomalyDetectionConfig,
    AuditEventType,
    AuditLogEntry,
    BinningConfig,
    BinningMethod,
    JobExecutionStatus,
    LineageRecord,
    MerchantCategory,
    MerchantMapping,
    PIIColumnConfig,
    PIITokenizationConfig,
    RiskLevel,
    TokenizationMethod,
    TransactionRecord,
    TransformationResult,
)


class TestPIIColumnConfig:
    """Tests for PIIColumnConfig model."""

    def test_create_deterministic_config(self):
        """Test creating deterministic tokenization config."""
        config = PIIColumnConfig(
            column_name="customer_id",
            method=TokenizationMethod.DETERMINISTIC,
            output_length=16,
        )
        assert config.column_name == "customer_id"
        assert config.method == TokenizationMethod.DETERMINISTIC
        assert config.output_length == 16

    def test_create_format_preserving_config(self):
        """Test creating format-preserving tokenization config."""
        config = PIIColumnConfig(
            column_name="card_number",
            method=TokenizationMethod.FORMAT_PRESERVING,
            preserve_prefix=4,
            preserve_suffix=4,
        )
        assert config.preserve_prefix == 4
        assert config.preserve_suffix == 4

    def test_invalid_output_length(self):
        """Test that invalid output length raises error."""
        with pytest.raises(ValidationError):
            PIIColumnConfig(
                column_name="test",
                method=TokenizationMethod.DETERMINISTIC,
                output_length=5,  # Too short
            )


class TestBinningConfig:
    """Tests for BinningConfig model."""

    def test_default_binning_config(self):
        """Test default binning configuration."""
        config = BinningConfig()
        assert config.method == BinningMethod.PERCENTILE
        assert config.column == "transaction_amount"
        assert len(config.percentiles) == 9
        assert len(config.labels) == 8

    def test_custom_binning_config(self):
        """Test custom binning configuration."""
        config = BinningConfig(
            method=BinningMethod.CUSTOM,
            custom_bins=[0, 100, 500, 1000, float("inf")],
            labels=["small", "medium", "large", "xlarge"],
        )
        assert config.method == BinningMethod.CUSTOM
        assert len(config.custom_bins) == 5


class TestMerchantMapping:
    """Tests for MerchantMapping model."""

    def test_get_known_category(self, merchant_mapping):
        """Test getting a known merchant category."""
        mapping = MerchantMapping(
            mappings={
                k: MerchantCategory(**v) for k, v in merchant_mapping.items()
            }
        )
        category = mapping.get_category("5411")
        assert category.category == "grocery_stores"
        assert category.risk_level == RiskLevel.LOW

    def test_get_unknown_category(self):
        """Test getting unknown merchant category returns default."""
        mapping = MerchantMapping()
        category = mapping.get_category("9999")
        assert category.category == "unknown"
        assert category.risk_level == RiskLevel.HIGH


class TestTransactionRecord:
    """Tests for TransactionRecord model."""

    def test_create_transaction(self, sample_transaction):
        """Test creating a transaction record."""
        txn = TransactionRecord(**sample_transaction)
        assert txn.transaction_id == "txn_001"
        assert txn.transaction_amount == Decimal("150.00")
        assert txn.currency == "CHF"

    def test_missing_required_field(self):
        """Test that missing required field raises error."""
        with pytest.raises(ValidationError):
            TransactionRecord(
                transaction_id="txn_001",
                customer_id="cust_001",
                # Missing transaction_amount, merchant_category_code, transaction_timestamp
            )


class TestTransformationResult:
    """Tests for TransformationResult model."""

    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        result = TransformationResult(
            success=True,
            records_input=1000,
            records_output=990,
            records_filtered=5,
            records_errored=5,
            transformation_type="pii_tokenization",
            duration_seconds=10.5,
        )
        assert result.error_rate == 0.005

    def test_zero_input_error_rate(self):
        """Test error rate with zero input."""
        result = TransformationResult(
            success=True,
            records_input=0,
            records_output=0,
            transformation_type="test",
            duration_seconds=0.1,
        )
        assert result.error_rate == 0.0


class TestLineageRecord:
    """Tests for LineageRecord model."""

    def test_create_lineage_record(self):
        """Test creating a lineage record."""
        record = LineageRecord(
            job_execution_id="jr_123",
            job_name="test-etl",
            start_time=datetime(2024, 1, 15, 10, 0, 0),
            status=JobExecutionStatus.SUCCEEDED,
            input_records=1000,
            output_records=990,
            transformations_applied=["pii_tokenization", "binning"],
            input_paths=["s3://bucket/input/"],
            output_paths=["s3://bucket/output/"],
        )
        assert record.job_execution_id == "jr_123"
        assert record.status == JobExecutionStatus.SUCCEEDED

    def test_to_catalog_metadata(self):
        """Test converting lineage to catalog metadata."""
        record = LineageRecord(
            job_execution_id="jr_123",
            job_name="test-etl",
            start_time=datetime(2024, 1, 15, 10, 0, 0),
            end_time=datetime(2024, 1, 15, 10, 15, 0),
            status=JobExecutionStatus.SUCCEEDED,
        )
        metadata = record.to_catalog_metadata()
        assert "job_execution_id" in metadata
        assert metadata["status"] == "SUCCEEDED"


class TestAuditLogEntry:
    """Tests for AuditLogEntry model."""

    def test_create_audit_entry(self):
        """Test creating an audit log entry."""
        entry = AuditLogEntry(
            event_type=AuditEventType.JOB_START,
            job_execution_id="jr_123",
            job_name="test-etl",
            action="StartJobRun",
            details={"trigger": "scheduled"},
        )
        assert entry.event_type == AuditEventType.JOB_START
        assert entry.status == "SUCCESS"

    def test_to_cloudwatch_log(self):
        """Test formatting audit entry for CloudWatch."""
        entry = AuditLogEntry(
            event_type=AuditEventType.PII_TOKENIZATION,
            job_execution_id="jr_123",
            details={"columns": ["customer_id", "email"]},
        )
        log_str = entry.to_cloudwatch_log()
        assert "PII_TOKENIZATION" in log_str
        assert "jr_123" in log_str


class TestAnomalyDetectionConfig:
    """Tests for AnomalyDetectionConfig model."""

    def test_default_config(self):
        """Test default anomaly detection configuration."""
        config = AnomalyDetectionConfig()
        assert config.contamination == 0.01
        assert config.n_estimators == 100
        assert config.random_state == 42

    def test_invalid_contamination(self):
        """Test that invalid contamination raises error."""
        with pytest.raises(ValidationError):
            AnomalyDetectionConfig(contamination=0.6)  # Too high
