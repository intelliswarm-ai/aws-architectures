# =============================================================================
# VPC Endpoints Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

# Subnet IDs for interface endpoints
variable "subnet_ids" {
  description = "Subnet IDs for interface endpoints"
  type        = list(string)
}

# Security group ID for interface endpoints
variable "security_group_id" {
  description = "Security group ID for interface endpoints"
  type        = string
}

# Route table IDs for gateway endpoints
variable "route_table_ids" {
  description = "Route table IDs for gateway endpoints"
  type        = list(string)
  default     = []
}

# Gateway Endpoints
variable "enable_s3_endpoint" {
  description = "Enable S3 gateway endpoint"
  type        = bool
  default     = true
}

variable "enable_dynamodb_endpoint" {
  description = "Enable DynamoDB gateway endpoint"
  type        = bool
  default     = true
}

# Interface Endpoints
variable "enable_secrets_manager_endpoint" {
  description = "Enable Secrets Manager interface endpoint"
  type        = bool
  default     = true
}

variable "enable_ssm_endpoint" {
  description = "Enable SSM interface endpoint"
  type        = bool
  default     = true
}

variable "enable_sqs_endpoint" {
  description = "Enable SQS interface endpoint"
  type        = bool
  default     = true
}

variable "enable_sns_endpoint" {
  description = "Enable SNS interface endpoint"
  type        = bool
  default     = true
}

variable "enable_kms_endpoint" {
  description = "Enable KMS interface endpoint"
  type        = bool
  default     = true
}

variable "enable_logs_endpoint" {
  description = "Enable CloudWatch Logs interface endpoint"
  type        = bool
  default     = true
}

variable "enable_events_endpoint" {
  description = "Enable EventBridge interface endpoint"
  type        = bool
  default     = true
}

variable "enable_bedrock_endpoint" {
  description = "Enable Bedrock interface endpoint"
  type        = bool
  default     = false
}

variable "enable_execute_api_endpoint" {
  description = "Enable API Gateway execute-api interface endpoint"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
