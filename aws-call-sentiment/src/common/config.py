"""Configuration settings for call sentiment analysis."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
    )

    # AWS Configuration
    aws_region: str = "eu-central-2"

    # S3 Buckets
    transcripts_bucket: str = "call-sentiment-transcripts"
    output_bucket: str = "call-sentiment-output"
    transcripts_prefix: str = "input/"
    output_prefix: str = "comprehend-output/"

    # OpenSearch
    opensearch_endpoint: str = ""
    opensearch_index_prefix: str = "call-sentiment"
    opensearch_transcripts_index: str = "call-sentiment-transcripts"
    opensearch_analytics_index: str = "call-sentiment-analytics"

    # Comprehend
    comprehend_role_arn: str = ""
    comprehend_job_prefix: str = "call-sentiment-job"
    default_language: str = "en"

    # API Configuration
    api_page_size: int = 20
    max_page_size: int = 100

    # Feature Flags
    enable_entity_extraction: bool = True
    enable_key_phrase_extraction: bool = True
    enable_per_segment_sentiment: bool = True
    enable_language_detection: bool = True

    # Logging
    log_level: str = "INFO"
    powertools_service_name: str = "call-sentiment"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
