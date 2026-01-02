variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.12"
}

variable "memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 256
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 60
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "log_level" {
  description = "Logging level"
  type        = string
  default     = "INFO"
}

# IAM Roles
variable "producer_role_arn" {
  description = "ARN of the producer IAM role"
  type        = string
}

variable "dashboard_consumer_role_arn" {
  description = "ARN of the dashboard consumer IAM role"
  type        = string
}

variable "geofence_consumer_role_arn" {
  description = "ARN of the geofence consumer IAM role"
  type        = string
}

variable "archive_consumer_role_arn" {
  description = "ARN of the archive consumer IAM role"
  type        = string
}

# Resource references
variable "kinesis_stream_name" {
  description = "Name of the Kinesis stream"
  type        = string
}

variable "kinesis_stream_arn" {
  description = "ARN of the Kinesis stream"
  type        = string
}

variable "positions_table_name" {
  description = "Name of the positions DynamoDB table"
  type        = string
}

variable "geofences_table_name" {
  description = "Name of the geofences DynamoDB table"
  type        = string
}

variable "archive_bucket_name" {
  description = "Name of the S3 archive bucket"
  type        = string
}

variable "alerts_topic_arn" {
  description = "ARN of the SNS alerts topic"
  type        = string
}

# Consumer configuration
variable "consumer_batch_size" {
  description = "Batch size for consumers"
  type        = number
  default     = 100
}

variable "consumer_parallelization" {
  description = "Parallelization factor for consumers"
  type        = number
  default     = 2
}

variable "consumer_starting_position" {
  description = "Starting position for consumers"
  type        = string
  default     = "LATEST"
}

variable "max_batching_window_seconds" {
  description = "Maximum batching window for consumers"
  type        = number
  default     = 5
}

# Producer configuration
variable "num_trucks" {
  description = "Number of simulated trucks"
  type        = number
  default     = 50
}

variable "batch_size" {
  description = "Batch size for producer"
  type        = number
  default     = 100
}

# Layer configuration
variable "create_layer" {
  description = "Create Lambda layer for dependencies"
  type        = bool
  default     = false
}

variable "layer_zip_path" {
  description = "Path to layer ZIP file"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
