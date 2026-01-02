variable "state_machine_name" {
  description = "Name of the Step Functions state machine"
  type        = string
}

variable "validate_task_lambda_arn" {
  description = "ARN of the validate task Lambda function"
  type        = string
}

variable "process_task_lambda_arn" {
  description = "ARN of the process task Lambda function"
  type        = string
}

variable "finalize_task_lambda_arn" {
  description = "ARN of the finalize task Lambda function"
  type        = string
}

variable "success_topic_arn" {
  description = "ARN of the success SNS topic"
  type        = string
}

variable "failure_topic_arn" {
  description = "ARN of the failure SNS topic"
  type        = string
}

variable "log_level" {
  description = "Logging level for state machine (OFF, ALL, ERROR, FATAL)"
  type        = string
  default     = "ERROR"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "enable_xray" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
