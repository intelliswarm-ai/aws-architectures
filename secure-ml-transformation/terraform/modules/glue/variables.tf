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

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "glue_security_group_id" {
  description = "Glue security group ID"
  type        = string
}

variable "glue_role_arn" {
  description = "Glue IAM role ARN"
  type        = string
}

variable "scripts_bucket" {
  description = "Scripts S3 bucket name"
  type        = string
}

variable "raw_data_bucket" {
  description = "Raw data S3 bucket name"
  type        = string
}

variable "processed_data_bucket" {
  description = "Processed data S3 bucket name"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
}

variable "glue_worker_type" {
  description = "Glue worker type"
  type        = string
  default     = "G.1X"
}

variable "glue_number_of_workers" {
  description = "Number of Glue workers"
  type        = number
  default     = 10
}

variable "glue_job_timeout" {
  description = "Glue job timeout in minutes"
  type        = number
  default     = 120
}
