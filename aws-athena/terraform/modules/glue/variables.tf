variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "database_name" {
  description = "Name of the Glue database"
  type        = string
}

variable "etl_job_name" {
  description = "Name of the ETL job"
  type        = string
}

variable "crawler_name" {
  description = "Name of the crawler"
  type        = string
}

variable "glue_role_arn" {
  description = "ARN of the Glue service role"
  type        = string
}

variable "raw_bucket_name" {
  description = "Name of the raw data bucket"
  type        = string
}

variable "processed_bucket_name" {
  description = "Name of the processed data bucket"
  type        = string
}

variable "etl_script_bucket" {
  description = "Bucket for ETL scripts"
  type        = string
}

variable "worker_type" {
  description = "Glue worker type"
  type        = string
  default     = "G.1X"
}

variable "number_of_workers" {
  description = "Number of Glue workers"
  type        = number
  default     = 2
}
