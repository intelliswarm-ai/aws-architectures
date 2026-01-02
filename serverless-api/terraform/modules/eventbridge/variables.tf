variable "rule_name" {
  description = "Name of the EventBridge rule"
  type        = string
}

variable "description" {
  description = "Description of the rule"
  type        = string
  default     = ""
}

variable "schedule_expression" {
  description = "Schedule expression (rate or cron)"
  type        = string
}

variable "lambda_arn" {
  description = "ARN of the Lambda function to invoke"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "enabled" {
  description = "Whether the rule is enabled"
  type        = bool
  default     = true
}

variable "maximum_event_age" {
  description = "Maximum age of event in seconds (60-86400)"
  type        = number
  default     = 3600
}

variable "maximum_retry_attempts" {
  description = "Maximum number of retry attempts (0-185)"
  type        = number
  default     = 2
}

variable "dlq_arn" {
  description = "ARN of the dead letter queue (optional)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
