################################################################################
# IAM Module Variables
################################################################################

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "sqs_queue_arn" {
  description = "ARN of the main SQS queue"
  type        = string
}

variable "sqs_dlq_arn" {
  description = "ARN of the SQS dead letter queue"
  type        = string
}

variable "dynamodb_table_arns" {
  description = "List of DynamoDB table ARNs"
  type        = list(string)
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
