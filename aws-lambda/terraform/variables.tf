variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-central-2"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "task-automation"
}

# Lambda Configuration
variable "lambda_memory_size" {
  description = "Default memory size for Lambda functions in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Default timeout for Lambda functions in seconds"
  type        = number
  default     = 30
}

variable "lambda_log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 14
}

# SQS Configuration
variable "sqs_visibility_timeout" {
  description = "SQS visibility timeout in seconds"
  type        = number
  default     = 60
}

variable "sqs_message_retention" {
  description = "SQS message retention period in seconds"
  type        = number
  default     = 1209600 # 14 days
}

variable "sqs_max_receive_count" {
  description = "Maximum number of times a message can be received before going to DLQ"
  type        = number
  default     = 3
}

# DynamoDB Configuration
variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "dynamodb_ttl_days" {
  description = "DynamoDB item TTL in days"
  type        = number
  default     = 7
}

# EventBridge Configuration
variable "task_generation_schedule" {
  description = "Schedule expression for task generation (rate or cron)"
  type        = string
  default     = "rate(5 minutes)"
}

# Notification Configuration
variable "notification_email" {
  description = "Email address for task notifications"
  type        = string
  default     = ""
}

variable "enable_email_notifications" {
  description = "Enable email notifications"
  type        = bool
  default     = false
}

# Lambda JAR paths
variable "lambda_jar_base_path" {
  description = "Base path for Lambda JAR files"
  type        = string
  default     = "../lambda"
}
