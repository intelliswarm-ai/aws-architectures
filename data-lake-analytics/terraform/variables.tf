# ---------------------------------------------------------------------------------------------------------------------
# REQUIRED PARAMETERS
# These parameters require values to be provided
# ---------------------------------------------------------------------------------------------------------------------

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "athena-datalake"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-2"
}

# ---------------------------------------------------------------------------------------------------------------------
# S3 CONFIGURATION
# ---------------------------------------------------------------------------------------------------------------------

variable "raw_bucket_name" {
  description = "Name of the S3 bucket for raw JSON data"
  type        = string
  default     = ""
}

variable "processed_bucket_name" {
  description = "Name of the S3 bucket for processed Parquet data"
  type        = string
  default     = ""
}

variable "results_bucket_name" {
  description = "Name of the S3 bucket for Athena query results"
  type        = string
  default     = ""
}

# ---------------------------------------------------------------------------------------------------------------------
# GLUE CONFIGURATION
# ---------------------------------------------------------------------------------------------------------------------

variable "glue_database_name" {
  description = "Name of the Glue database"
  type        = string
  default     = "analytics_db"
}

variable "glue_etl_job_name" {
  description = "Name of the Glue ETL job"
  type        = string
  default     = "json-to-parquet"
}

variable "glue_crawler_name" {
  description = "Name of the Glue crawler"
  type        = string
  default     = "parquet-crawler"
}

variable "glue_worker_type" {
  description = "Glue worker type (G.1X, G.2X, G.4X)"
  type        = string
  default     = "G.1X"
}

variable "glue_number_of_workers" {
  description = "Number of Glue workers"
  type        = number
  default     = 2
}

# ---------------------------------------------------------------------------------------------------------------------
# ATHENA CONFIGURATION
# ---------------------------------------------------------------------------------------------------------------------

variable "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  type        = string
  default     = "analytics"
}

variable "athena_query_timeout" {
  description = "Athena query timeout in seconds"
  type        = number
  default     = 300
}

variable "athena_bytes_scanned_cutoff" {
  description = "Maximum bytes scanned per query (cost control)"
  type        = number
  default     = 10737418240 # 10 GB
}

# ---------------------------------------------------------------------------------------------------------------------
# LAKE FORMATION CONFIGURATION
# ---------------------------------------------------------------------------------------------------------------------

variable "lakeformation_admin_arns" {
  description = "List of IAM ARNs for Lake Formation administrators"
  type        = list(string)
  default     = []
}

variable "enable_lakeformation" {
  description = "Enable Lake Formation for fine-grained access control"
  type        = bool
  default     = true
}

# ---------------------------------------------------------------------------------------------------------------------
# LAMBDA CONFIGURATION
# ---------------------------------------------------------------------------------------------------------------------

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions in MB"
  type        = number
  default     = 256
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions in seconds"
  type        = number
  default     = 60
}

variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.11"
}

# ---------------------------------------------------------------------------------------------------------------------
# EVENTBRIDGE CONFIGURATION
# ---------------------------------------------------------------------------------------------------------------------

variable "etl_schedule_expression" {
  description = "Schedule expression for ETL job (cron or rate)"
  type        = string
  default     = "rate(1 hour)"
}

variable "enable_scheduled_etl" {
  description = "Enable scheduled ETL job execution"
  type        = bool
  default     = true
}

# ---------------------------------------------------------------------------------------------------------------------
# TAGS
# ---------------------------------------------------------------------------------------------------------------------

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
