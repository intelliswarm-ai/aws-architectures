variable "project_prefix" {
  description = "Project name prefix"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "api_handler_arn" {
  description = "API handler Lambda ARN"
  type        = string
}

variable "api_handler_name" {
  description = "API handler Lambda function name"
  type        = string
}

variable "agent_handler_arn" {
  description = "Agent handler Lambda ARN"
  type        = string
}

variable "agent_handler_name" {
  description = "Agent handler Lambda function name"
  type        = string
}

variable "throttle_rate_limit" {
  description = "Throttle rate limit"
  type        = number
  default     = 100
}

variable "throttle_burst_limit" {
  description = "Throttle burst limit"
  type        = number
  default     = 200
}

variable "enable_logging" {
  description = "Enable API Gateway logging"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
