# =============================================================================
# AWS Budgets Module Variables
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

# Budget Configuration
variable "budget_limit" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 100
}

variable "budget_time_unit" {
  description = "Budget time unit (MONTHLY, QUARTERLY, ANNUALLY)"
  type        = string
  default     = "MONTHLY"
}

# Alert Configuration
variable "notification_email" {
  description = "Email address for budget alerts"
  type        = string
  default     = ""
}

variable "notification_threshold_50" {
  description = "Enable 50% threshold notification"
  type        = bool
  default     = true
}

variable "notification_threshold_80" {
  description = "Enable 80% threshold notification"
  type        = bool
  default     = true
}

variable "notification_threshold_100" {
  description = "Enable 100% threshold notification"
  type        = bool
  default     = true
}

variable "notification_threshold_forecast" {
  description = "Enable forecasted 100% threshold notification"
  type        = bool
  default     = true
}

# Service-specific Budgets
variable "enable_lambda_budget" {
  description = "Enable Lambda-specific budget"
  type        = bool
  default     = false
}

variable "lambda_budget_limit" {
  description = "Lambda budget limit in USD"
  type        = number
  default     = 50
}

variable "enable_dynamodb_budget" {
  description = "Enable DynamoDB-specific budget"
  type        = bool
  default     = false
}

variable "dynamodb_budget_limit" {
  description = "DynamoDB budget limit in USD"
  type        = number
  default     = 20
}

variable "enable_api_gateway_budget" {
  description = "Enable API Gateway-specific budget"
  type        = bool
  default     = false
}

variable "api_gateway_budget_limit" {
  description = "API Gateway budget limit in USD"
  type        = number
  default     = 10
}

# Cost Allocation Tags
variable "cost_allocation_tag" {
  description = "Cost allocation tag key for filtering"
  type        = string
  default     = "Project"
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
