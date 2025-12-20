# =============================================================================
# CloudTrail Module Variables
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

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
  default     = null
}

# Trail Configuration
variable "is_multi_region" {
  description = "Enable multi-region trail"
  type        = bool
  default     = true
}

variable "enable_log_file_validation" {
  description = "Enable log file integrity validation"
  type        = bool
  default     = true
}

variable "include_global_service_events" {
  description = "Include global service events (IAM, etc.)"
  type        = bool
  default     = true
}

# S3 Configuration
variable "s3_bucket_name" {
  description = "S3 bucket name for CloudTrail logs (created if not provided)"
  type        = string
  default     = ""
}

variable "s3_key_prefix" {
  description = "S3 key prefix for CloudTrail logs"
  type        = string
  default     = "cloudtrail"
}

variable "log_retention_days" {
  description = "S3 log retention in days (0 for no expiration)"
  type        = number
  default     = 90
}

# CloudWatch Logs Integration
variable "enable_cloudwatch_logs" {
  description = "Enable CloudWatch Logs integration"
  type        = bool
  default     = true
}

variable "cloudwatch_log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# Event Selectors
variable "enable_management_events" {
  description = "Log management events"
  type        = bool
  default     = true
}

variable "management_event_read_write" {
  description = "Management events to log (All, ReadOnly, WriteOnly)"
  type        = string
  default     = "All"
}

variable "enable_data_events" {
  description = "Enable data events logging"
  type        = bool
  default     = false
}

variable "data_event_s3_buckets" {
  description = "S3 bucket ARNs for data events (empty for all)"
  type        = list(string)
  default     = []
}

variable "data_event_lambda_functions" {
  description = "Lambda function ARNs for data events (empty for all)"
  type        = list(string)
  default     = []
}

variable "data_event_dynamodb_tables" {
  description = "DynamoDB table ARNs for data events"
  type        = list(string)
  default     = []
}

# Insights
variable "enable_insights" {
  description = "Enable CloudTrail Insights"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
