variable "project_prefix" {
  description = "Project prefix for resource naming"
  type        = string
}

variable "lambda_role_arn" {
  description = "Lambda execution role ARN"
  type        = string
}

variable "environment_variables" {
  description = "Environment variables for Lambda functions"
  type        = map(string)
  default     = {}
}

variable "source_path" {
  description = "Path to Lambda deployment package"
  type        = string
}

variable "memory_size" {
  description = "Memory size in MB"
  type        = number
  default     = 512
}

variable "timeout" {
  description = "Function timeout in seconds"
  type        = number
  default     = 60
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
