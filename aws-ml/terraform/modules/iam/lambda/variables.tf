variable "project_prefix" {
  type = string
}

variable "raw_bucket_arn" {
  type = string
}

variable "processed_bucket_arn" {
  type = string
}

variable "model_bucket_arn" {
  type = string
}

variable "documents_table_arn" {
  type = string
}

variable "processing_queue_arn" {
  type = string
}

variable "dlq_arn" {
  type = string
}

variable "success_topic_arn" {
  type = string
}

variable "failure_topic_arn" {
  type = string
}

variable "alert_topic_arn" {
  type = string
}

variable "workflow_arn" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
