variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "stream_name" {
  description = "Name of the Kinesis stream"
  type        = string
}

variable "shard_count" {
  description = "Number of shards"
  type        = number
  default     = 4
}

variable "retention_period" {
  description = "Data retention period in hours"
  type        = number
  default     = 24
}

variable "stream_mode" {
  description = "Stream mode (PROVISIONED or ON_DEMAND)"
  type        = string
  default     = "PROVISIONED"
}

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
  default     = ""
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
