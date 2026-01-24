variable "project_prefix" {
  description = "Project prefix for resource naming"
  type        = string
}

variable "execution_role_arn" {
  description = "SageMaker execution role ARN"
  type        = string
}

variable "model_bucket_name" {
  description = "S3 bucket name for model artifacts"
  type        = string
}

variable "initial_model_data" {
  description = "S3 URI for initial model artifacts"
  type        = string
  default     = ""
}

variable "instance_type" {
  description = "SageMaker endpoint instance type"
  type        = string
  default     = "ml.m5.xlarge"
}

variable "initial_instance_count" {
  description = "Initial number of instances"
  type        = number
  default     = 1
}

variable "enable_auto_scaling" {
  description = "Enable auto-scaling"
  type        = bool
  default     = true
}

variable "min_capacity" {
  description = "Minimum instance count for auto-scaling"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum instance count for auto-scaling"
  type        = number
  default     = 10
}

variable "target_invocations" {
  description = "Target invocations per instance"
  type        = number
  default     = 1000
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
