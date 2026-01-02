variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "producer_lambda_arn" {
  description = "ARN of the producer Lambda function"
  type        = string
}

variable "schedule_expression" {
  description = "Schedule expression for the producer"
  type        = string
  default     = "rate(1 minute)"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
