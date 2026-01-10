"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    # AWS Configuration
    aws_region: str = "eu-central-2"
    environment: str = "dev"

    # Bedrock Configuration
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    bedrock_max_tokens: int = 4096
    bedrock_temperature: float = 0.0

    # Knowledge Base Configuration
    knowledge_base_id: str = ""
    knowledge_base_data_source_id: str = ""

    # OpenSearch Serverless Configuration
    opensearch_collection_endpoint: str = ""
    opensearch_collection_name: str = ""
    opensearch_index_name: str = "knowledge-index"
    opensearch_vector_dimension: int = 1024

    # S3 Configuration
    documents_bucket: str = ""
    processed_bucket: str = ""

    # DynamoDB Configuration
    documents_table: str = ""
    conversations_table: str = ""

    # RAG Configuration
    retrieval_top_k: int = 5
    retrieval_score_threshold: float = 0.7
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Agent Configuration
    agent_id: str = ""
    agent_alias_id: str = ""
    enable_agent: bool = True

    # API Configuration
    api_rate_limit: int = 100
    api_burst_limit: int = 200

    # Observability
    log_level: str = "INFO"
    powertools_service_name: str = "genai-knowledge-assistant"
    powertools_metrics_namespace: str = "GenAIKnowledgeAssistant"
    enable_xray: bool = True

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "prod"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
