variable "project_prefix" {
  description = "Project name prefix"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
}

variable "documents_bucket_arn" {
  description = "Documents S3 bucket ARN"
  type        = string
}

variable "documents_bucket_name" {
  description = "Documents S3 bucket name"
  type        = string
}

variable "opensearch_collection_arn" {
  description = "OpenSearch collection ARN"
  type        = string
}

variable "opensearch_collection_endpoint" {
  description = "OpenSearch collection endpoint"
  type        = string
}

variable "embedding_model_id" {
  description = "Bedrock embedding model ID"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "foundation_model_id" {
  description = "Bedrock foundation model ID for agent"
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "vector_dimension" {
  description = "Vector dimension"
  type        = number
  default     = 1024
}

variable "chunk_size" {
  description = "Document chunk size"
  type        = number
  default     = 1000
}

variable "chunk_overlap" {
  description = "Chunk overlap"
  type        = number
  default     = 200
}

variable "create_agent" {
  description = "Whether to create Bedrock Agent"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
