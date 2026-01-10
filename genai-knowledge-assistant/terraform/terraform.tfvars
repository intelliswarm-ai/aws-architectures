# =============================================================================
# GenAI Knowledge Assistant - Terraform Variables
# =============================================================================

# Project Configuration
project_name = "genai-assistant"
environment  = "dev"
aws_region   = "eu-central-2"

# Bedrock Configuration
bedrock_model_id           = "anthropic.claude-3-5-sonnet-20241022-v2:0"
bedrock_embedding_model_id = "amazon.titan-embed-text-v2:0"
enable_bedrock_agent       = true

# Knowledge Base Configuration
create_knowledge_base = true
vector_dimension      = 1024
chunk_size            = 1000
chunk_overlap         = 200

# OpenSearch Configuration
opensearch_collection_name  = "knowledge-vectors"
opensearch_standby_replicas = false  # Set to true for production

# Lambda Configuration
lambda_memory_size        = 512
lambda_timeout            = 60
lambda_log_retention_days = 30
enable_xray               = true

# API Gateway Configuration
api_throttle_rate_limit  = 100
api_throttle_burst_limit = 200
enable_api_logging       = true

# Storage Configuration
documents_bucket_name = ""  # Leave empty for auto-generated name
enable_s3_versioning  = true

# Additional Tags
tags = {
  Owner      = "Platform Team"
  CostCenter = "GenAI"
}
