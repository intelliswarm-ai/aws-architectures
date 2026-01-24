################################################################################
# General Configuration
################################################################################

variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
  default     = "secure-ml-transform"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-central-2"  # Zurich
}

################################################################################
# Network Configuration
################################################################################

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
  default     = ["eu-central-2a", "eu-central-2b"]
}

################################################################################
# Glue Configuration
################################################################################

variable "glue_worker_type" {
  description = "Glue worker type"
  type        = string
  default     = "G.1X"

  validation {
    condition     = contains(["Standard", "G.1X", "G.2X"], var.glue_worker_type)
    error_message = "Worker type must be Standard, G.1X, or G.2X."
  }
}

variable "glue_number_of_workers" {
  description = "Number of Glue workers"
  type        = number
  default     = 10

  validation {
    condition     = var.glue_number_of_workers >= 2 && var.glue_number_of_workers <= 100
    error_message = "Number of workers must be between 2 and 100."
  }
}

variable "glue_job_timeout" {
  description = "Glue job timeout in minutes"
  type        = number
  default     = 120

  validation {
    condition     = var.glue_job_timeout >= 1 && var.glue_job_timeout <= 2880
    error_message = "Job timeout must be between 1 and 2880 minutes."
  }
}

################################################################################
# Logging Configuration
################################################################################

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 90

  validation {
    condition     = contains([30, 60, 90, 180, 365], var.log_retention_days)
    error_message = "Log retention must be 30, 60, 90, 180, or 365 days."
  }
}

################################################################################
# PII Configuration
################################################################################

variable "pii_columns" {
  description = "Comma-separated list of PII columns"
  type        = string
  default     = "customer_id,account_number,card_number,email,phone"
}

variable "binning_method" {
  description = "Amount binning method"
  type        = string
  default     = "percentile"

  validation {
    condition     = contains(["percentile", "quantile", "custom"], var.binning_method)
    error_message = "Binning method must be percentile, quantile, or custom."
  }
}

variable "anomaly_contamination" {
  description = "Isolation Forest contamination parameter"
  type        = number
  default     = 0.01

  validation {
    condition     = var.anomaly_contamination >= 0.001 && var.anomaly_contamination <= 0.5
    error_message = "Contamination must be between 0.001 and 0.5."
  }
}
