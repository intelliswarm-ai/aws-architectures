################################################################################
# CloudWatch Module Variables
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

variable "log_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 30
}

variable "sqs_queue_name" {
  description = "Name of the SQS queue"
  type        = string
}

variable "dlq_name" {
  description = "Name of the dead letter queue"
  type        = string
}

variable "asg_name" {
  description = "Name of the Auto Scaling Group"
  type        = string
}

variable "lambda_function_names" {
  description = "List of Lambda function names"
  type        = list(string)
  default     = []
}

variable "target_messages_per_instance" {
  description = "Target messages per instance for scaling"
  type        = number
  default     = 100
}

variable "queue_depth_threshold" {
  description = "Queue depth threshold for alarm"
  type        = number
  default     = 1000
}

variable "message_age_threshold_seconds" {
  description = "Maximum message age in seconds before alarm"
  type        = number
  default     = 300
}

variable "dlq_message_threshold" {
  description = "DLQ message count threshold for alarm"
  type        = number
  default     = 10
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 2
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications"
  type        = string
  default     = ""
}

variable "scale_out_policy_arn" {
  description = "ARN of the scale-out policy"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
