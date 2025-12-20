# =============================================================================
# AWS Config Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

# S3 Configuration
variable "s3_bucket_name" {
  description = "S3 bucket name for Config logs (created if not provided)"
  type        = string
  default     = ""
}

variable "s3_key_prefix" {
  description = "S3 key prefix for Config logs"
  type        = string
  default     = "config"
}

variable "log_retention_days" {
  description = "S3 log retention in days"
  type        = number
  default     = 90
}

# Recording Configuration
variable "recording_enabled" {
  description = "Enable configuration recording"
  type        = bool
  default     = true
}

variable "all_supported" {
  description = "Record all supported resource types"
  type        = bool
  default     = true
}

variable "include_global_resources" {
  description = "Include global resources (IAM, etc.)"
  type        = bool
  default     = true
}

variable "resource_types" {
  description = "Specific resource types to record (if all_supported is false)"
  type        = list(string)
  default     = []
}

# Managed Rules
variable "enable_encrypted_volumes" {
  description = "Enable encrypted-volumes rule"
  type        = bool
  default     = true
}

variable "enable_s3_bucket_encryption" {
  description = "Enable s3-bucket-server-side-encryption-enabled rule"
  type        = bool
  default     = true
}

variable "enable_root_mfa" {
  description = "Enable root-account-mfa-enabled rule"
  type        = bool
  default     = true
}

variable "enable_iam_password_policy" {
  description = "Enable iam-password-policy rule"
  type        = bool
  default     = true
}

variable "enable_rds_encryption" {
  description = "Enable rds-storage-encrypted rule"
  type        = bool
  default     = true
}

variable "enable_cloudtrail_enabled" {
  description = "Enable cloudtrail-enabled rule"
  type        = bool
  default     = true
}

variable "enable_lambda_concurrency" {
  description = "Enable lambda-concurrency-check rule"
  type        = bool
  default     = false
}

variable "enable_dynamodb_autoscaling" {
  description = "Enable dynamodb-autoscaling-enabled rule"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
