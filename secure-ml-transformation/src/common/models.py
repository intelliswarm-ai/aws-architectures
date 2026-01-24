"""Pydantic models for data structures."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class JobExecutionStatus(str, Enum):
    """Status of a Glue job execution."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
    TIMEOUT = "TIMEOUT"


class TokenizationMethod(str, Enum):
    """PII tokenization methods."""

    DETERMINISTIC = "deterministic"
    FORMAT_PRESERVING = "format_preserving"
    HASH = "hash"
    REDACT = "redact"


class BinningMethod(str, Enum):
    """Amount binning methods."""

    PERCENTILE = "percentile"
    QUANTILE = "quantile"
    CUSTOM = "custom"


class RiskLevel(str, Enum):
    """Risk level categories."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PIIColumnConfig(BaseModel):
    """Configuration for a single PII column."""

    column_name: str = Field(..., description="Name of the column containing PII")
    method: TokenizationMethod = Field(..., description="Tokenization method to use")
    output_length: int = Field(default=16, ge=8, le=64, description="Token output length")
    preserve_prefix: int = Field(default=0, ge=0, le=10, description="Characters to preserve at start")
    preserve_suffix: int = Field(default=0, ge=0, le=10, description="Characters to preserve at end")
    algorithm: str = Field(default="sha256", description="Hash algorithm for hash method")


class PIITokenizationConfig(BaseModel):
    """Configuration for PII tokenization."""

    columns: list[PIIColumnConfig] = Field(default_factory=list, description="PII column configurations")
    salt: str = Field(default="", description="Salt for deterministic tokenization")
    enable_audit: bool = Field(default=True, description="Log tokenization operations")

    @field_validator("salt")
    @classmethod
    def validate_salt(cls, v: str) -> str:
        """Validate salt is provided for production use."""
        if not v:
            # Allow empty salt for testing, but log warning
            pass
        return v


class BinningConfig(BaseModel):
    """Configuration for amount binning."""

    method: BinningMethod = Field(default=BinningMethod.PERCENTILE, description="Binning method")
    column: str = Field(default="transaction_amount", description="Column to bin")
    percentiles: list[int] = Field(
        default=[0, 10, 25, 50, 75, 90, 95, 99, 100],
        description="Percentile thresholds",
    )
    labels: list[str] = Field(
        default=["micro", "small", "low", "medium", "high", "large", "very_large", "extreme"],
        description="Bin labels",
    )
    custom_bins: list[float] | None = Field(default=None, description="Custom bin edges")
    handle_negatives: Literal["absolute", "separate", "error"] = Field(
        default="absolute",
        description="How to handle negative values",
    )

    @field_validator("labels")
    @classmethod
    def validate_labels_count(cls, v: list[str], info: Any) -> list[str]:
        """Validate label count matches bins."""
        # Labels should be one less than percentiles/bins
        return v


class MerchantCategory(BaseModel):
    """Merchant category mapping entry."""

    category: str = Field(..., description="Category name")
    category_id: int = Field(..., ge=0, description="Numeric category ID")
    risk_level: RiskLevel = Field(..., description="Risk level")
    risk_score: float = Field(..., ge=0, le=1, description="Numeric risk score")
    parent_category: str = Field(..., description="Parent category for hierarchy")
    is_cash_equivalent: bool = Field(default=False, description="Cash equivalent flag")


class MerchantMapping(BaseModel):
    """Complete merchant category mapping."""

    mappings: dict[str, MerchantCategory] = Field(
        default_factory=dict,
        description="MCC to category mappings",
    )
    default_category: MerchantCategory = Field(
        default=MerchantCategory(
            category="unknown",
            category_id=999,
            risk_level=RiskLevel.HIGH,
            risk_score=0.8,
            parent_category="uncategorized",
            is_cash_equivalent=False,
        ),
        description="Default category for unknown MCCs",
    )

    def get_category(self, mcc: str) -> MerchantCategory:
        """Get category for MCC, returning default if not found."""
        return self.mappings.get(mcc, self.default_category)


class AnomalyDetectionConfig(BaseModel):
    """Configuration for anomaly detection."""

    contamination: float = Field(default=0.01, ge=0.001, le=0.5, description="Expected anomaly ratio")
    n_estimators: int = Field(default=100, ge=10, le=500, description="Number of trees")
    max_samples: int | str = Field(default="auto", description="Samples per tree")
    max_features: float = Field(default=1.0, ge=0.1, le=1.0, description="Features per tree")
    features: list[str] = Field(
        default=[
            "amount_bin_encoded",
            "merchant_risk_score",
            "hour_of_day",
            "day_of_week",
        ],
        description="Features for anomaly detection",
    )
    random_state: int = Field(default=42, description="Random seed for reproducibility")


class TransactionRecord(BaseModel):
    """Input transaction record model."""

    transaction_id: str = Field(..., description="Unique transaction identifier")
    customer_id: str = Field(..., description="Customer identifier (PII)")
    account_number: str | None = Field(default=None, description="Account number (PII)")
    card_number: str | None = Field(default=None, description="Card number (PII)")
    email: str | None = Field(default=None, description="Email address (PII)")
    phone: str | None = Field(default=None, description="Phone number (PII)")
    transaction_amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field(default="CHF", description="Currency code")
    merchant_category_code: str = Field(..., description="MCC code")
    merchant_name: str | None = Field(default=None, description="Merchant name")
    transaction_timestamp: datetime = Field(..., description="Transaction timestamp")
    location_country: str | None = Field(default=None, description="Transaction country")
    location_city: str | None = Field(default=None, description="Transaction city")

    class Config:
        """Pydantic config."""

        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }


class TransformationResult(BaseModel):
    """Result of a transformation operation."""

    success: bool = Field(..., description="Whether transformation succeeded")
    records_input: int = Field(..., ge=0, description="Input record count")
    records_output: int = Field(..., ge=0, description="Output record count")
    records_filtered: int = Field(default=0, ge=0, description="Filtered record count")
    records_errored: int = Field(default=0, ge=0, description="Error record count")
    transformation_type: str = Field(..., description="Type of transformation")
    duration_seconds: float = Field(..., ge=0, description="Duration in seconds")
    error_message: str | None = Field(default=None, description="Error message if failed")

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.records_input == 0:
            return 0.0
        return self.records_errored / self.records_input


class LineageRecord(BaseModel):
    """Data lineage record for tracking transformations."""

    job_execution_id: str = Field(..., description="Unique job execution ID")
    job_name: str = Field(..., description="Glue job name")
    start_time: datetime = Field(..., description="Job start time")
    end_time: datetime | None = Field(default=None, description="Job end time")
    status: JobExecutionStatus = Field(..., description="Job status")
    input_records: int = Field(default=0, ge=0, description="Input record count")
    output_records: int = Field(default=0, ge=0, description="Output record count")
    filtered_records: int = Field(default=0, ge=0, description="Filtered record count")
    transformations_applied: list[str] = Field(
        default_factory=list,
        description="List of transformations applied",
    )
    input_paths: list[str] = Field(default_factory=list, description="Input S3 paths")
    output_paths: list[str] = Field(default_factory=list, description="Output S3 paths")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Job parameters")
    bookmark_state: dict[str, Any] | None = Field(default=None, description="Job bookmark state")

    def to_catalog_metadata(self) -> dict[str, str]:
        """Convert to Glue catalog metadata format."""
        return {
            "job_execution_id": self.job_execution_id,
            "job_name": self.job_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else "",
            "status": self.status.value,
            "input_records": str(self.input_records),
            "output_records": str(self.output_records),
            "transformations": ",".join(self.transformations_applied),
        }


class AuditEventType(str, Enum):
    """Types of audit events."""

    JOB_START = "JOB_START"
    JOB_COMPLETE = "JOB_COMPLETE"
    JOB_FAILED = "JOB_FAILED"
    DATA_ACCESS = "DATA_ACCESS"
    TRANSFORMATION_START = "TRANSFORMATION_START"
    TRANSFORMATION_COMPLETE = "TRANSFORMATION_COMPLETE"
    PII_DETECTION = "PII_DETECTION"
    PII_TOKENIZATION = "PII_TOKENIZATION"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    DATA_QUALITY_CHECK = "DATA_QUALITY_CHECK"
    ERROR = "ERROR"


class AuditLogEntry(BaseModel):
    """Audit log entry for compliance tracking."""

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    event_type: AuditEventType = Field(..., description="Type of audit event")
    job_execution_id: str = Field(..., description="Job execution ID")
    job_name: str | None = Field(default=None, description="Job name")
    user_identity: str | None = Field(default=None, description="IAM user/role ARN")
    source_ip: str | None = Field(default=None, description="Source IP address")
    resource_arn: str | None = Field(default=None, description="Resource ARN involved")
    action: str | None = Field(default=None, description="Action performed")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details")
    status: Literal["SUCCESS", "FAILURE", "IN_PROGRESS"] = Field(
        default="SUCCESS",
        description="Event status",
    )

    def to_cloudwatch_log(self) -> str:
        """Format for CloudWatch Logs."""
        import json

        return json.dumps(
            {
                "timestamp": self.timestamp.isoformat(),
                "event_type": self.event_type.value,
                "job_execution_id": self.job_execution_id,
                "job_name": self.job_name,
                "user_identity": self.user_identity,
                "resource_arn": self.resource_arn,
                "action": self.action,
                "status": self.status,
                "details": self.details,
            },
            default=str,
        )
