# =============================================================================
# Secrets Manager Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
  default     = null
}

# Secrets Configuration
variable "secrets" {
  description = "Map of secrets to create"
  type = map(object({
    description       = string
    secret_string     = optional(string)
    secret_binary     = optional(string)
    recovery_days     = optional(number, 7)
    enable_rotation   = optional(bool, false)
    rotation_days     = optional(number, 30)
    rotation_lambda_arn = optional(string)
  }))
  default = {}
}

# Multi-tenant secrets (per-tenant integrations)
variable "tenant_secrets" {
  description = "Create tenant-specific secret placeholders"
  type = map(object({
    description = string
    template    = map(string)  # Template for tenant secrets
  }))
  default = {}
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
