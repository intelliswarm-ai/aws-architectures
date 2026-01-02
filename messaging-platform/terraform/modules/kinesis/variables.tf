################################################################################
# Kinesis Module - Variables
################################################################################

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "stream_name" {
  description = "Name of the Kinesis stream"
  type        = string
}

variable "shard_count" {
  description = "Number of shards"
  type        = number
  default     = 2
}

variable "retention_period" {
  description = "Retention period in hours (max 8760 = 365 days)"
  type        = number
  default     = 8760

  validation {
    condition     = var.retention_period >= 24 && var.retention_period <= 8760
    error_message = "Retention period must be between 24 and 8760 hours."
  }
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
