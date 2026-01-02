variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "kinesis_stream_name" {
  description = "Name of the Kinesis stream"
  type        = string
}

variable "lambda_function_names" {
  description = "List of Lambda function names to monitor"
  type        = list(string)
}

variable "error_threshold" {
  description = "Error count threshold for alarms"
  type        = number
  default     = 5
}

variable "duration_threshold_ms" {
  description = "Duration threshold in milliseconds for alarms"
  type        = number
  default     = 30000
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
