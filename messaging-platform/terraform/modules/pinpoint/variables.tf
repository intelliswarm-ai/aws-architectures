################################################################################
# Pinpoint Module - Variables
################################################################################

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "kinesis_stream_arn" {
  description = "ARN of the Kinesis stream for event streaming"
  type        = string
}

variable "kinesis_role_arn" {
  description = "ARN of the IAM role for Pinpoint to write to Kinesis"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
