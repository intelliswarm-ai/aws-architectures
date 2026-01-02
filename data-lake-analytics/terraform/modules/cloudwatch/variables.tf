variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "lambda_functions" {
  description = "List of Lambda function names"
  type        = list(string)
}

variable "glue_job_name" {
  description = "Name of the Glue ETL job"
  type        = string
}

variable "athena_workgroup" {
  description = "Name of the Athena workgroup"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "error_threshold" {
  description = "Error threshold for alarms"
  type        = number
  default     = 5
}

variable "athena_bytes_threshold" {
  description = "Athena bytes scanned threshold for cost alarm (10GB default)"
  type        = number
  default     = 10737418240
}

variable "alarm_actions" {
  description = "List of ARNs for alarm actions (e.g., SNS topics)"
  type        = list(string)
  default     = []
}

variable "ok_actions" {
  description = "List of ARNs for OK actions"
  type        = list(string)
  default     = []
}
