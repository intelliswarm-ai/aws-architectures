"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AWS Configuration
    aws_region: str = Field(default="eu-central-2", description="AWS region (Zurich)")
    environment: Literal["dev", "staging", "prod"] = Field(
        default="dev", description="Deployment environment"
    )
    project_name: str = Field(
        default="secure-ml-transform", description="Project name prefix"
    )

    # S3 Configuration
    raw_data_bucket: str = Field(
        default="", description="S3 bucket for raw transaction data"
    )
    processed_data_bucket: str = Field(
        default="", description="S3 bucket for processed ML-ready data"
    )
    config_bucket: str = Field(
        default="", description="S3 bucket for configuration files"
    )
    merchant_mapping_key: str = Field(
        default="config/merchant_mapping.json",
        description="S3 key for merchant category mapping",
    )

    # KMS Configuration
    kms_key_alias: str = Field(
        default="alias/secure-ml-transform", description="KMS key alias for encryption"
    )
    kms_key_id: str = Field(default="", description="KMS key ID")

    # Glue Configuration
    glue_database: str = Field(
        default="secure_ml_transform_db", description="Glue catalog database name"
    )
    glue_connection_name: str = Field(
        default="", description="Glue VPC connection name"
    )
    glue_security_configuration: str = Field(
        default="", description="Glue security configuration name"
    )

    # DataBrew Configuration
    databrew_project_name: str = Field(
        default="", description="DataBrew project name"
    )

    # PII Tokenization Configuration
    pii_salt: str = Field(
        default="", description="Salt for deterministic PII tokenization"
    )
    pii_columns: str = Field(
        default="customer_id,account_number,card_number,email,phone",
        description="Comma-separated list of PII columns",
    )

    # Binning Configuration
    binning_method: Literal["percentile", "quantile", "custom"] = Field(
        default="percentile", description="Amount binning method"
    )
    binning_percentiles: str = Field(
        default="0,10,25,50,75,90,95,99,100",
        description="Comma-separated percentile thresholds",
    )

    # Anomaly Detection Configuration
    anomaly_contamination: float = Field(
        default=0.01, ge=0.001, le=0.5, description="Isolation Forest contamination"
    )
    anomaly_n_estimators: int = Field(
        default=100, ge=10, le=500, description="Number of trees in Isolation Forest"
    )

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    log_retention_days: int = Field(
        default=90, ge=1, le=365, description="CloudWatch log retention in days"
    )

    # Data Quality Configuration
    max_error_rate: float = Field(
        default=0.01, ge=0, le=1, description="Maximum allowed error rate"
    )
    enable_data_quality_checks: bool = Field(
        default=True, description="Enable data quality validation"
    )

    @property
    def pii_column_list(self) -> list[str]:
        """Parse PII columns from comma-separated string."""
        return [col.strip() for col in self.pii_columns.split(",") if col.strip()]

    @property
    def binning_percentile_list(self) -> list[int]:
        """Parse binning percentiles from comma-separated string."""
        return [int(p.strip()) for p in self.binning_percentiles.split(",")]

    @property
    def resource_prefix(self) -> str:
        """Generate resource naming prefix."""
        return f"{self.project_name}-{self.environment}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
