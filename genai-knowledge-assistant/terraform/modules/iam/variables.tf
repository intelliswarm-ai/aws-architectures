variable "project_prefix" {
  description = "Project name prefix"
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

variable "documents_table_arn" {
  description = "Documents DynamoDB table ARN"
  type        = string
}

variable "conversations_table_arn" {
  description = "Conversations DynamoDB table ARN"
  type        = string
}

variable "opensearch_collection_arn" {
  description = "OpenSearch collection ARN"
  type        = string
}

variable "bedrock_model_id" {
  description = "Bedrock foundation model ID"
  type        = string
}

variable "bedrock_embedding_model_id" {
  description = "Bedrock embedding model ID"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
