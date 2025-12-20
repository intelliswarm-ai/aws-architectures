variable "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "lambda_function_names" {
  description = "List of Lambda function names to monitor"
  type        = list(string)
}

variable "queue_name" {
  description = "Name of the SQS queue to monitor"
  type        = string
}

variable "dlq_name" {
  description = "Name of the dead letter queue to monitor"
  type        = string
}

variable "table_name" {
  description = "Name of the DynamoDB table to monitor"
  type        = string
}

variable "state_machine_arn" {
  description = "ARN of the Step Functions state machine"
  type        = string
}

variable "state_machine_name" {
  description = "Name of the Step Functions state machine"
  type        = string
}

variable "alarm_sns_topic_arns" {
  description = "List of SNS topic ARNs for alarm notifications"
  type        = list(string)
  default     = []
}

variable "lambda_error_threshold" {
  description = "Threshold for Lambda error alarm"
  type        = number
  default     = 5
}

variable "queue_depth_threshold" {
  description = "Threshold for SQS queue depth alarm"
  type        = number
  default     = 100
}

variable "sfn_failure_threshold" {
  description = "Threshold for Step Functions failure alarm"
  type        = number
  default     = 5
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
