variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "app_name" {
  description = "Application name for email templates"
  type        = string
  default     = "Enterprise API"
}

variable "password_min_length" {
  description = "Minimum password length"
  type        = number
  default     = 12
}

variable "mfa_configuration" {
  description = "MFA configuration: OFF, ON, or OPTIONAL"
  type        = string
  default     = "OPTIONAL"
}

variable "advanced_security_mode" {
  description = "Advanced security mode: OFF, AUDIT, or ENFORCED"
  type        = string
  default     = "AUDIT"
}

variable "domain_prefix" {
  description = "Cognito domain prefix (leave empty for auto-generated)"
  type        = string
  default     = ""
}

variable "callback_urls" {
  description = "Allowed callback URLs"
  type        = list(string)
  default     = ["https://localhost:3000/callback"]
}

variable "logout_urls" {
  description = "Allowed logout URLs"
  type        = list(string)
  default     = ["https://localhost:3000/logout"]
}

variable "access_token_validity_hours" {
  description = "Access token validity in hours"
  type        = number
  default     = 1
}

variable "id_token_validity_hours" {
  description = "ID token validity in hours"
  type        = number
  default     = 1
}

variable "refresh_token_validity_days" {
  description = "Refresh token validity in days"
  type        = number
  default     = 30
}

variable "resource_server_scopes" {
  description = "Custom OAuth scopes for resource server"
  type = list(object({
    name        = string
    description = string
  }))
  default = []
}

variable "create_identity_pool" {
  description = "Create Cognito Identity Pool"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
