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

variable "raw_data_bucket_arn" {
  description = "Raw data bucket ARN"
  type        = string
}

variable "processed_data_bucket_arn" {
  description = "Processed data bucket ARN"
  type        = string
}

variable "scripts_bucket_arn" {
  description = "Scripts bucket ARN"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN"
  type        = string
}
