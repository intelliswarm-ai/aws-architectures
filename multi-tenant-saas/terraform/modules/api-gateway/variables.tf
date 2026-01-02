# =============================================================================
# API Gateway Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "api_name" {
  description = "API Gateway name"
  type        = string
}

variable "api_description" {
  description = "API Gateway description"
  type        = string
  default     = "Enterprise API Gateway"
}

# Stage Configuration
variable "stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "v1"
}

variable "stage_variables" {
  description = "Stage variables"
  type        = map(string)
  default     = {}
}

# Logging
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "enable_access_logging" {
  description = "Enable API Gateway access logging"
  type        = bool
  default     = true
}

variable "enable_request_validation" {
  description = "Enable request validation"
  type        = bool
  default     = true
}

# Throttling
variable "throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 100
}

variable "throttling_rate_limit" {
  description = "API Gateway throttling rate limit"
  type        = number
  default     = 50
}

# Authorization
variable "cognito_user_pool_arn" {
  description = "Cognito User Pool ARN for authorization"
  type        = string
  default     = null
}

variable "enable_cognito_authorizer" {
  description = "Enable Cognito authorizer"
  type        = bool
  default     = false
}

variable "lambda_authorizer_arn" {
  description = "Lambda authorizer function ARN"
  type        = string
  default     = null
}

variable "lambda_authorizer_invoke_arn" {
  description = "Lambda authorizer invoke ARN"
  type        = string
  default     = null
}

variable "enable_lambda_authorizer" {
  description = "Enable Lambda authorizer"
  type        = bool
  default     = false
}

variable "authorizer_result_ttl" {
  description = "Authorizer result TTL in seconds"
  type        = number
  default     = 300
}

# API Keys and Usage Plans
variable "enable_api_key" {
  description = "Enable API key requirement"
  type        = bool
  default     = false
}

variable "usage_plan_quota_limit" {
  description = "Usage plan quota limit (requests per period)"
  type        = number
  default     = 10000
}

variable "usage_plan_quota_period" {
  description = "Usage plan quota period (DAY, WEEK, MONTH)"
  type        = string
  default     = "MONTH"
}

# Lambda Integration
variable "lambda_function_arn" {
  description = "Lambda function ARN for integration"
  type        = string
}

variable "lambda_function_invoke_arn" {
  description = "Lambda function invoke ARN"
  type        = string
}

# WAF
variable "waf_acl_arn" {
  description = "WAF ACL ARN to associate"
  type        = string
  default     = null
}

# CORS
variable "enable_cors" {
  description = "Enable CORS"
  type        = bool
  default     = true
}

variable "cors_allow_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}

variable "cors_allow_methods" {
  description = "CORS allowed methods"
  type        = list(string)
  default     = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
}

variable "cors_allow_headers" {
  description = "CORS allowed headers"
  type        = list(string)
  default     = ["Content-Type", "Authorization", "X-Api-Key", "X-Amz-Date", "X-Amz-Security-Token"]
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
