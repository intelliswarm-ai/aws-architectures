# =============================================================================
# AWS Serverless Enterprise Platform - Variables
# =============================================================================

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------

variable "aws_region" {
  description = "AWS region"
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
  default     = "enterprise-api"
}

variable "log_level" {
  description = "Logging level"
  type        = string
  default     = "INFO"
}

# -----------------------------------------------------------------------------
# VPC Configuration
# -----------------------------------------------------------------------------

variable "enable_vpc" {
  description = "Enable VPC deployment for Lambda"
  type        = bool
  default     = false
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "multi_az" {
  description = "Deploy across multiple availability zones"
  type        = bool
  default     = false
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC flow logs"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Security Configuration
# -----------------------------------------------------------------------------

variable "enable_encryption" {
  description = "Enable KMS encryption for all resources"
  type        = bool
  default     = true
}

variable "enable_cognito" {
  description = "Enable Cognito authentication"
  type        = bool
  default     = true
}

variable "password_min_length" {
  description = "Minimum password length for Cognito"
  type        = number
  default     = 12
}

variable "mfa_configuration" {
  description = "MFA configuration: OFF, ON, or OPTIONAL"
  type        = string
  default     = "OPTIONAL"
}

variable "cognito_callback_urls" {
  description = "Cognito callback URLs"
  type        = list(string)
  default     = ["https://localhost:3000/callback"]
}

variable "cognito_logout_urls" {
  description = "Cognito logout URLs"
  type        = list(string)
  default     = ["https://localhost:3000/logout"]
}

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "create_database_resources" {
  description = "Create RDS database resources"
  type        = bool
  default     = false
}

variable "create_cache_resources" {
  description = "Create ElastiCache resources"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Monitoring Configuration
# -----------------------------------------------------------------------------

variable "enable_audit_logging" {
  description = "Enable audit logging to DynamoDB"
  type        = bool
  default     = true
}

variable "enable_request_validation" {
  description = "Enable API request validation"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "notification_email" {
  description = "Email for notifications"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# Lambda Configuration
# -----------------------------------------------------------------------------

variable "lambda_memory_size" {
  description = "Default Lambda memory size in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Default Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_package_path" {
  description = "Path to Lambda deployment package"
  type        = string
  default     = "../dist/lambda.zip"
}

# -----------------------------------------------------------------------------
# WAF Configuration
# -----------------------------------------------------------------------------

variable "enable_waf" {
  description = "Enable WAF for API Gateway"
  type        = bool
  default     = false
}

variable "waf_rate_limit" {
  description = "WAF rate limit per 5 minutes per IP"
  type        = number
  default     = 2000
}

# -----------------------------------------------------------------------------
# Compliance Configuration
# -----------------------------------------------------------------------------

variable "enable_config" {
  description = "Enable AWS Config for compliance monitoring"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Cost Management
# -----------------------------------------------------------------------------

variable "budget_limit" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 100
}
