variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "name_prefix" {
  description = "Name prefix for resources"
  type        = string
}

variable "log_retention_days" {
  description = "Log retention in days"
  type        = number
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
}
