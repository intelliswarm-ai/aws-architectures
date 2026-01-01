################################################################################
# Lambda Module - Variables
################################################################################

variable "project_name" {
  description = "Name of the project"
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

# IAM Roles
variable "event_processor_role_arn" {
  description = "ARN of the event processor Lambda role"
  type        = string
}

variable "response_handler_role_arn" {
  description = "ARN of the response handler Lambda role"
  type        = string
}

variable "analytics_processor_role_arn" {
  description = "ARN of the analytics processor Lambda role"
  type        = string
}

variable "archive_consumer_role_arn" {
  description = "ARN of the archive consumer Lambda role"
  type        = string
}

# Resource Names/ARNs
variable "kinesis_stream_name" {
  description = "Name of the Kinesis stream"
  type        = string
}

variable "kinesis_stream_arn" {
  description = "ARN of the Kinesis stream"
  type        = string
}

variable "responses_table_name" {
  description = "Name of the responses DynamoDB table"
  type        = string
}

variable "subscribers_table_name" {
  description = "Name of the subscribers DynamoDB table"
  type        = string
}

variable "archive_bucket_name" {
  description = "Name of the archive S3 bucket"
  type        = string
}

variable "notifications_topic_arn" {
  description = "ARN of the notifications SNS topic"
  type        = string
}

variable "pinpoint_app_id" {
  description = "Pinpoint application ID"
  type        = string
}

# Consumer Configuration
variable "consumer_batch_size" {
  description = "Batch size for Kinesis consumers"
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

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
