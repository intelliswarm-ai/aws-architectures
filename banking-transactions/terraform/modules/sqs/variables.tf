################################################################################
# SQS Module Variables
################################################################################

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
}

variable "visibility_timeout" {
  description = "Visibility timeout for messages in seconds"
  type        = number
  default     = 60
}

variable "message_retention_seconds" {
  description = "Message retention period in seconds"
  type        = number
  default     = 1209600  # 14 days
}

variable "dlq_retention_seconds" {
  description = "DLQ message retention period in seconds"
  type        = number
  default     = 1209600  # 14 days
}

variable "max_receive_count" {
  description = "Maximum number of receives before sending to DLQ"
  type        = number
  default     = 3
}

variable "ec2_role_arn" {
  description = "ARN of the EC2 IAM role for queue access"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
