################################################################################
# SMS Marketing System - Variables
################################################################################

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-central-2"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "sms-marketing"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

################################################################################
# Kinesis Configuration
################################################################################

variable "kinesis_shard_count" {
  description = "Number of shards for Kinesis stream"
  type        = number
  default     = 2

  validation {
    condition     = var.kinesis_shard_count >= 1 && var.kinesis_shard_count <= 200
    error_message = "Shard count must be between 1 and 200."
  }
}

variable "kinesis_retention_hours" {
  description = "Data retention period in hours (365 days = 8760 hours)"
  type        = number
  default     = 8760  # 365 days

  validation {
    condition     = var.kinesis_retention_hours >= 24 && var.kinesis_retention_hours <= 8760
    error_message = "Retention must be between 24 and 8760 hours (365 days max)."
  }
}

################################################################################
# Lambda Configuration
################################################################################

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions (MB)"
  type        = number
  default     = 256

  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Memory must be between 128 and 10240 MB."
  }
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions (seconds)"
  type        = number
  default     = 60

  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Timeout must be between 1 and 900 seconds."
  }
}

################################################################################
# Consumer Configuration
################################################################################

variable "consumer_batch_size" {
  description = "Batch size for Kinesis consumers"
  type        = number
  default     = 100

  validation {
    condition     = var.consumer_batch_size >= 1 && var.consumer_batch_size <= 10000
    error_message = "Batch size must be between 1 and 10000."
  }
}

variable "consumer_parallelization" {
  description = "Parallelization factor for consumers"
  type        = number
  default     = 2

  validation {
    condition     = var.consumer_parallelization >= 1 && var.consumer_parallelization <= 10
    error_message = "Parallelization must be between 1 and 10."
  }
}

variable "consumer_starting_position" {
  description = "Starting position for consumers"
  type        = string
  default     = "LATEST"

  validation {
    condition     = contains(["LATEST", "TRIM_HORIZON"], var.consumer_starting_position)
    error_message = "Starting position must be LATEST or TRIM_HORIZON."
  }
}

variable "max_batching_window_seconds" {
  description = "Maximum batching window for consumers"
  type        = number
  default     = 5

  validation {
    condition     = var.max_batching_window_seconds >= 0 && var.max_batching_window_seconds <= 300
    error_message = "Batching window must be between 0 and 300 seconds."
  }
}

################################################################################
# Pinpoint Configuration
################################################################################

variable "sms_sender_id" {
  description = "SMS Sender ID (alphanumeric, max 11 chars)"
  type        = string
  default     = "MARKETING"

  validation {
    condition     = length(var.sms_sender_id) <= 11
    error_message = "Sender ID must be 11 characters or less."
  }
}

variable "sms_message_type" {
  description = "Default SMS message type"
  type        = string
  default     = "PROMOTIONAL"

  validation {
    condition     = contains(["PROMOTIONAL", "TRANSACTIONAL"], var.sms_message_type)
    error_message = "Message type must be PROMOTIONAL or TRANSACTIONAL."
  }
}
