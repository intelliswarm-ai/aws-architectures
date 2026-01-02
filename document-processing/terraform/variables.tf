# =============================================================================
# General Configuration
# =============================================================================

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
  description = "Project name for resource naming"
  type        = string
  default     = "ml-platform"
}

# =============================================================================
# Lambda Configuration
# =============================================================================

variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.12"
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "lambda_package_path" {
  description = "Path to Lambda deployment package"
  type        = string
  default     = "../dist/lambda.zip"
}

# =============================================================================
# S3 Configuration
# =============================================================================

variable "raw_bucket_name" {
  description = "S3 bucket for raw documents (leave empty for auto-generated)"
  type        = string
  default     = ""
}

variable "processed_bucket_name" {
  description = "S3 bucket for processed documents (leave empty for auto-generated)"
  type        = string
  default     = ""
}

variable "model_bucket_name" {
  description = "S3 bucket for ML model artifacts (leave empty for auto-generated)"
  type        = string
  default     = ""
}

# =============================================================================
# DynamoDB Configuration
# =============================================================================

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PAY_PER_REQUEST or PROVISIONED)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "dynamodb_read_capacity" {
  description = "DynamoDB read capacity (only for PROVISIONED)"
  type        = number
  default     = 5
}

variable "dynamodb_write_capacity" {
  description = "DynamoDB write capacity (only for PROVISIONED)"
  type        = number
  default     = 5
}

# =============================================================================
# SQS Configuration
# =============================================================================

variable "sqs_visibility_timeout" {
  description = "SQS visibility timeout in seconds"
  type        = number
  default     = 120
}

variable "sqs_message_retention" {
  description = "SQS message retention in seconds"
  type        = number
  default     = 1209600 # 14 days
}

variable "sqs_max_receive_count" {
  description = "Max receive count before moving to DLQ"
  type        = number
  default     = 3
}

# =============================================================================
# SageMaker Configuration
# =============================================================================

variable "sagemaker_endpoint_instance_type" {
  description = "Instance type for SageMaker endpoint"
  type        = string
  default     = "ml.m5.large"
}

variable "sagemaker_endpoint_instance_count" {
  description = "Number of instances for SageMaker endpoint"
  type        = number
  default     = 1
}

variable "training_instance_type" {
  description = "Instance type for SageMaker training jobs"
  type        = string
  default     = "ml.m5.xlarge"
}

variable "create_sagemaker_endpoint" {
  description = "Whether to create SageMaker endpoint"
  type        = bool
  default     = false
}

# =============================================================================
# Bedrock Configuration
# =============================================================================

variable "bedrock_model_id" {
  description = "Bedrock foundation model ID"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "bedrock_max_tokens" {
  description = "Maximum tokens for Bedrock generation"
  type        = number
  default     = 4096
}

# =============================================================================
# Notification Configuration
# =============================================================================

variable "notification_email" {
  description = "Email address for notifications"
  type        = string
  default     = ""
}

variable "enable_email_notifications" {
  description = "Enable email notifications"
  type        = bool
  default     = false
}

# =============================================================================
# Feature Flags
# =============================================================================

variable "enable_pii_detection" {
  description = "Enable PII detection with Comprehend"
  type        = bool
  default     = true
}

variable "enable_moderation" {
  description = "Enable content moderation with Rekognition"
  type        = bool
  default     = true
}

variable "enable_summarization" {
  description = "Enable document summarization with Bedrock"
  type        = bool
  default     = true
}

variable "enable_qa_generation" {
  description = "Enable Q&A generation with Bedrock"
  type        = bool
  default     = true
}
