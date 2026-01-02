variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "workgroup_name" {
  description = "Name of the Athena workgroup"
  type        = string
}

variable "results_bucket_name" {
  description = "S3 bucket for query results"
  type        = string
}

variable "database_name" {
  description = "Name of the Glue database"
  type        = string
}

variable "query_timeout" {
  description = "Query timeout in seconds"
  type        = number
  default     = 300
}

variable "bytes_scanned_cutoff" {
  description = "Maximum bytes scanned per query"
  type        = number
  default     = 10737418240 # 10 GB
}
