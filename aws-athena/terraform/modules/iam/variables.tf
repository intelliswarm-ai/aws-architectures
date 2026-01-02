variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "raw_bucket_arn" {
  description = "ARN of the raw data bucket"
  type        = string
}

variable "processed_bucket_arn" {
  description = "ARN of the processed data bucket"
  type        = string
}

variable "results_bucket_arn" {
  description = "ARN of the results bucket"
  type        = string
}

variable "glue_database_name" {
  description = "Name of the Glue database"
  type        = string
}

variable "enable_lakeformation" {
  description = "Enable Lake Formation permissions"
  type        = bool
  default     = true
}
