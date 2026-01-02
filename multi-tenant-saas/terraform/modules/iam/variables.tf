# =============================================================================
# IAM Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name for resource naming"
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

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

# Permission Boundaries
variable "enable_permission_boundary" {
  description = "Enable permission boundary for all roles"
  type        = bool
  default     = true
}

variable "allowed_regions" {
  description = "List of allowed AWS regions"
  type        = list(string)
  default     = ["eu-central-2"]
}

variable "denied_services" {
  description = "List of denied AWS services"
  type        = list(string)
  default     = ["organizations", "account"]
}

# Cross-Account Access
variable "enable_cross_account" {
  description = "Enable cross-account access patterns"
  type        = bool
  default     = false
}

variable "trusted_account_ids" {
  description = "List of trusted AWS account IDs for cross-account access"
  type        = list(string)
  default     = []
}

variable "external_id" {
  description = "External ID for cross-account assume role"
  type        = string
  default     = ""
  sensitive   = true
}

# KMS Key ARN for encryption
variable "kms_key_arn" {
  description = "KMS key ARN for encryption operations"
  type        = string
  default     = null
}

# DynamoDB Tables
variable "dynamodb_table_arns" {
  description = "DynamoDB table ARNs for access"
  type        = list(string)
  default     = []
}

# SQS Queues
variable "sqs_queue_arns" {
  description = "SQS queue ARNs for access"
  type        = list(string)
  default     = []
}

# SNS Topics
variable "sns_topic_arns" {
  description = "SNS topic ARNs for access"
  type        = list(string)
  default     = []
}

# S3 Buckets
variable "s3_bucket_arns" {
  description = "S3 bucket ARNs for access"
  type        = list(string)
  default     = []
}

# Secrets Manager
variable "secrets_arns" {
  description = "Secrets Manager secret ARNs for access"
  type        = list(string)
  default     = []
}

# SSM Parameters
variable "ssm_parameter_arns" {
  description = "SSM Parameter Store ARNs for access"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
