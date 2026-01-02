variable "project_prefix" {
  type = string
}

variable "validate_lambda_arn" {
  type = string
}

variable "route_lambda_arn" {
  type = string
}

variable "extraction_lambda_arn" {
  type = string
}

variable "transcription_lambda_arn" {
  type = string
}

variable "analysis_lambda_arn" {
  type = string
}

variable "inference_lambda_arn" {
  type = string
}

variable "bedrock_lambda_arn" {
  type = string
}

variable "finalize_lambda_arn" {
  type = string
}

variable "success_topic_arn" {
  type = string
}

variable "failure_topic_arn" {
  type = string
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "tags" {
  type    = map(string)
  default = {}
}
