variable "topic_prefix" {
  description = "Prefix for SNS topic names"
  type        = string
}

variable "kms_key_id" {
  description = "KMS key ID for SNS encryption (optional)"
  type        = string
  default     = null
}

variable "email_endpoint" {
  description = "Email address for notifications"
  type        = string
  default     = ""
}

variable "lambda_endpoint_arn" {
  description = "Lambda function ARN for notifications"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
