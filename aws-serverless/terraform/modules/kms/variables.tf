# =============================================================================
# KMS Module Variables
# =============================================================================

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "deletion_window_days" {
  description = "Key deletion window in days (7-30)"
  type        = number
  default     = 30
}

variable "enable_key_rotation" {
  description = "Enable automatic key rotation"
  type        = bool
  default     = true
}

variable "multi_region" {
  description = "Create a multi-region key"
  type        = bool
  default     = false
}

variable "admin_role_arns" {
  description = "ARNs of roles that can administer the key"
  type        = list(string)
  default     = []
}

variable "usage_role_arns" {
  description = "ARNs of roles that can use the key for encryption/decryption"
  type        = list(string)
  default     = []
}

variable "allow_aws_services" {
  description = "Allow AWS services (CloudWatch, SNS, SQS, Secrets Manager) to use the key"
  type        = bool
  default     = true
}

variable "cross_account_principals" {
  description = "ARNs of principals in other accounts that can use the key"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
