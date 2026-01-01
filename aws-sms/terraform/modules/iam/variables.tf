################################################################################
# IAM Module - Variables
################################################################################

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "kinesis_stream_arn" {
  description = "ARN of the Kinesis stream"
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

variable "sns_topic_arn" {
  description = "ARN of the SNS topic"
  type        = string
}

variable "pinpoint_app_arn" {
  description = "ARN of the Pinpoint application"
  type        = string
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
