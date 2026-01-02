variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
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

variable "results_bucket_name" {
  description = "Name of the results bucket"
  type        = string
}
