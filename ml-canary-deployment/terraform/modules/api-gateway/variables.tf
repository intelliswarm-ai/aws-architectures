variable "project_prefix" {
  description = "Project prefix for resource naming"
  type        = string
}

variable "inference_lambda_arn" {
  description = "Inference Lambda function ARN"
  type        = string
}

variable "inference_lambda_name" {
  description = "Inference Lambda function name"
  type        = string
}

variable "deployment_lambda_arn" {
  description = "Deployment Lambda function ARN"
  type        = string
}

variable "deployment_lambda_name" {
  description = "Deployment Lambda function name"
  type        = string
}

variable "traffic_shift_lambda_arn" {
  description = "Traffic shift Lambda function ARN"
  type        = string
}

variable "traffic_shift_lambda_name" {
  description = "Traffic shift Lambda function name"
  type        = string
}

variable "rollback_lambda_arn" {
  description = "Rollback Lambda function ARN"
  type        = string
}

variable "rollback_lambda_name" {
  description = "Rollback Lambda function name"
  type        = string
}

variable "stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
