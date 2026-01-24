# Variables for ML Canary Deployment

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-central-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "ml-canary-deployment"
}

# SageMaker Configuration
variable "sagemaker_instance_type" {
  description = "SageMaker endpoint instance type"
  type        = string
  default     = "ml.m5.xlarge"
}

variable "sagemaker_initial_instance_count" {
  description = "Initial number of instances for the endpoint"
  type        = number
  default     = 1
}

variable "initial_model_data" {
  description = "S3 URI for initial model artifacts (optional)"
  type        = string
  default     = ""
}

# Auto-scaling Configuration
variable "enable_auto_scaling" {
  description = "Enable auto-scaling for endpoint variants"
  type        = bool
  default     = true
}

variable "autoscaling_min_capacity" {
  description = "Minimum instance count for auto-scaling"
  type        = number
  default     = 1
}

variable "autoscaling_max_capacity" {
  description = "Maximum instance count for auto-scaling"
  type        = number
  default     = 10
}

variable "autoscaling_target_invocations" {
  description = "Target invocations per instance for scaling"
  type        = number
  default     = 1000
}

# Monitoring Thresholds
variable "latency_threshold_ms" {
  description = "Maximum acceptable P99 latency in milliseconds"
  type        = number
  default     = 100

  validation {
    condition     = var.latency_threshold_ms > 0 && var.latency_threshold_ms <= 30000
    error_message = "Latency threshold must be between 1 and 30000 ms."
  }
}

variable "error_rate_threshold" {
  description = "Maximum acceptable error rate (0.0 to 1.0)"
  type        = number
  default     = 0.01

  validation {
    condition     = var.error_rate_threshold >= 0 && var.error_rate_threshold <= 1
    error_message = "Error rate threshold must be between 0 and 1."
  }
}

variable "enable_auto_rollback" {
  description = "Enable automatic rollback when thresholds are exceeded"
  type        = bool
  default     = true
}

# Lambda Configuration
variable "lambda_source_path" {
  description = "Path to Lambda deployment package"
  type        = string
  default     = "../dist/lambda.zip"
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions (MB)"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions (seconds)"
  type        = number
  default     = 60
}

# Notification Configuration
variable "alert_email" {
  description = "Email address for deployment alerts"
  type        = string
  default     = ""
}

# Logging Configuration
variable "log_level" {
  description = "Log level for Lambda functions"
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR."
  }
}
