# =============================================================================
# Lambda Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "function_name" {
  description = "Lambda function name"
  type        = string
}

variable "handler" {
  description = "Lambda handler (module.function)"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.12"
}

variable "memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 256
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "source_path" {
  description = "Path to the Lambda deployment package"
  type        = string
}

variable "environment_variables" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
  default     = {}
}

variable "kms_key_arn" {
  description = "KMS key ARN for environment variable encryption"
  type        = string
  default     = null
}

# VPC Configuration
variable "vpc_enabled" {
  description = "Enable VPC deployment"
  type        = bool
  default     = false
}

variable "subnet_ids" {
  description = "Subnet IDs for VPC deployment"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security group IDs for VPC deployment"
  type        = list(string)
  default     = []
}

# IAM
variable "role_arn" {
  description = "IAM role ARN for the Lambda function (if not creating)"
  type        = string
  default     = null
}

variable "create_role" {
  description = "Create IAM role for Lambda"
  type        = bool
  default     = true
}

variable "additional_policies" {
  description = "Additional IAM policy ARNs to attach to the Lambda role"
  type        = list(string)
  default     = []
}

variable "inline_policy" {
  description = "Inline IAM policy document for the Lambda role"
  type        = string
  default     = null
}

# Reserved Concurrency
variable "reserved_concurrent_executions" {
  description = "Reserved concurrent executions (-1 for unreserved)"
  type        = number
  default     = -1
}

# Layers
variable "layers" {
  description = "Lambda layer ARNs"
  type        = list(string)
  default     = []
}

# Dead Letter Queue
variable "dead_letter_target_arn" {
  description = "ARN of SQS queue or SNS topic for dead letter"
  type        = string
  default     = null
}

# Tracing
variable "tracing_mode" {
  description = "X-Ray tracing mode (Active or PassThrough)"
  type        = string
  default     = "Active"
}

# CloudWatch Logs
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
