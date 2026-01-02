variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "schedule_expression" {
  description = "Schedule expression for ETL trigger"
  type        = string
  default     = "rate(1 hour)"
}

variable "etl_lambda_arn" {
  description = "ARN of the ETL Lambda function"
  type        = string
}

variable "etl_lambda_name" {
  description = "Name of the ETL Lambda function"
  type        = string
}
