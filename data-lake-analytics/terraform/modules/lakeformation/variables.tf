variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "admin_arns" {
  description = "List of IAM ARNs for Lake Formation administrators"
  type        = list(string)
}

variable "raw_bucket_arn" {
  description = "ARN of the raw data bucket"
  type        = string
}

variable "processed_bucket_arn" {
  description = "ARN of the processed data bucket"
  type        = string
}

variable "database_name" {
  description = "Name of the Glue database"
  type        = string
}

variable "glue_role_arn" {
  description = "ARN of the Glue service role"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  type        = string
}

variable "lakeformation_role_arn" {
  description = "ARN of the Lake Formation service role"
  type        = string
  default     = null
}
