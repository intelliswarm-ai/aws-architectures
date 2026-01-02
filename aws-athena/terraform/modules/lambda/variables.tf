variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  type        = string
}

variable "memory_size" {
  description = "Memory size in MB"
  type        = number
  default     = 256
}

variable "timeout" {
  description = "Timeout in seconds"
  type        = number
  default     = 60
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.11"
}

variable "raw_bucket_name" {
  description = "Name of the raw data bucket"
  type        = string
}

variable "processed_bucket_name" {
  description = "Name of the processed data bucket"
  type        = string
}

variable "results_bucket_name" {
  description = "Name of the results bucket"
  type        = string
}

variable "glue_database" {
  description = "Name of the Glue database"
  type        = string
}

variable "athena_workgroup" {
  description = "Name of the Athena workgroup"
  type        = string
}

variable "glue_etl_job_name" {
  description = "Name of the Glue ETL job"
  type        = string
}

variable "glue_crawler_name" {
  description = "Name of the Glue crawler"
  type        = string
}

variable "athena_query_timeout" {
  description = "Athena query timeout in seconds"
  type        = number
  default     = 300
}

variable "log_level" {
  description = "Log level for Lambda functions"
  type        = string
  default     = "INFO"
}
