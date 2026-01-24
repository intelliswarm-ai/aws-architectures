variable "project_prefix" {
  description = "Project prefix for resource naming"
  type        = string
}

variable "model_bucket_arn" {
  description = "ARN of model artifacts bucket"
  type        = string
}

variable "logs_bucket_arn" {
  description = "ARN of logs bucket"
  type        = string
}

variable "deployments_table_arn" {
  description = "ARN of deployments DynamoDB table"
  type        = string
}

variable "metrics_table_arn" {
  description = "ARN of metrics DynamoDB table"
  type        = string
}

variable "events_table_arn" {
  description = "ARN of events DynamoDB table"
  type        = string
}

variable "alerts_topic_arn" {
  description = "ARN of alerts SNS topic"
  type        = string
}

variable "events_topic_arn" {
  description = "ARN of events SNS topic"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
