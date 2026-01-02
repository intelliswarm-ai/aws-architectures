"""Configuration settings for AWS Athena data lake analytics."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AWS Configuration
    aws_region: str = Field(default="eu-central-2", alias="AWS_REGION")

    # S3 Configuration
    raw_bucket: str = Field(default="", alias="RAW_BUCKET")
    processed_bucket: str = Field(default="", alias="PROCESSED_BUCKET")
    results_bucket: str = Field(default="", alias="RESULTS_BUCKET")

    # Glue Configuration
    glue_database: str = Field(default="analytics_db", alias="GLUE_DATABASE")
    glue_raw_table: str = Field(default="raw_events", alias="GLUE_RAW_TABLE")
    glue_processed_table: str = Field(default="events", alias="GLUE_PROCESSED_TABLE")
    glue_etl_job_name: str = Field(default="json-to-parquet", alias="GLUE_ETL_JOB_NAME")
    glue_crawler_name: str = Field(default="parquet-crawler", alias="GLUE_CRAWLER_NAME")

    # Athena Configuration
    athena_workgroup: str = Field(default="analytics", alias="ATHENA_WORKGROUP")
    athena_query_timeout: int = Field(default=300, alias="ATHENA_QUERY_TIMEOUT")

    # Lake Formation
    lakeformation_admin_arn: str = Field(default="", alias="LAKEFORMATION_ADMIN_ARN")

    # Processing Configuration
    partition_columns: list[str] = Field(
        default=["year", "month", "day", "hour"], alias="PARTITION_COLUMNS"
    )
    target_format: str = Field(default="parquet", alias="TARGET_FORMAT")
    compression: str = Field(default="snappy", alias="COMPRESSION")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
