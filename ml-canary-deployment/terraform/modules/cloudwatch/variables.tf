variable "project_prefix" {
  description = "Project prefix for resource naming"
  type        = string
}

variable "endpoint_name" {
  description = "SageMaker endpoint name to monitor"
  type        = string
}

variable "latency_threshold_ms" {
  description = "Maximum acceptable P99 latency in milliseconds"
  type        = number
  default     = 100
}

variable "error_rate_threshold" {
  description = "Maximum acceptable error rate (0.0 to 1.0)"
  type        = number
  default     = 0.01
}

variable "alerts_topic_arn" {
  description = "SNS topic ARN for alerts"
  type        = string
}

variable "monitoring_lambda_arn" {
  description = "Monitoring Lambda function ARN"
  type        = string
}

variable "monitoring_lambda_name" {
  description = "Monitoring Lambda function name"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
