# =============================================================================
# Project Configuration
# =============================================================================

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "genai-assistant"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-2"
}

# =============================================================================
# Bedrock Configuration
# =============================================================================

variable "bedrock_model_id" {
  description = "Bedrock foundation model ID for text generation"
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "bedrock_embedding_model_id" {
  description = "Bedrock embedding model ID"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "enable_bedrock_agent" {
  description = "Whether to create a Bedrock Agent"
  type        = bool
  default     = true
}

# =============================================================================
# Knowledge Base Configuration
# =============================================================================

variable "create_knowledge_base" {
  description = "Whether to create a Bedrock Knowledge Base"
  type        = bool
  default     = true
}

variable "vector_dimension" {
  description = "Vector dimension for embeddings"
  type        = number
  default     = 1024
}

variable "chunk_size" {
  description = "Document chunk size in characters"
  type        = number
  default     = 1000
}

variable "chunk_overlap" {
  description = "Chunk overlap in characters"
  type        = number
  default     = 200
}

# =============================================================================
# OpenSearch Serverless Configuration
# =============================================================================

variable "opensearch_collection_name" {
  description = "OpenSearch Serverless collection name"
  type        = string
  default     = "knowledge-vectors"
}

variable "opensearch_standby_replicas" {
  description = "Enable standby replicas for OpenSearch"
  type        = bool
  default     = false
}

# =============================================================================
# Lambda Configuration
# =============================================================================

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions (MB)"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions (seconds)"
  type        = number
  default     = 60
}

variable "lambda_log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "enable_xray" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

# =============================================================================
# API Gateway Configuration
# =============================================================================

variable "api_throttle_rate_limit" {
  description = "API Gateway throttle rate limit"
  type        = number
  default     = 100
}

variable "api_throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 200
}

variable "enable_api_logging" {
  description = "Enable API Gateway access logging"
  type        = bool
  default     = true
}

# =============================================================================
# Storage Configuration
# =============================================================================

variable "documents_bucket_name" {
  description = "S3 bucket name for document storage (leave empty for auto-generated)"
  type        = string
  default     = ""
}

variable "enable_s3_versioning" {
  description = "Enable S3 bucket versioning"
  type        = bool
  default     = true
}

# =============================================================================
# Tags
# =============================================================================

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}
