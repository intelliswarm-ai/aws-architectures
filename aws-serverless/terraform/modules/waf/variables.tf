# =============================================================================
# WAF Module Variables
# =============================================================================

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "scope" {
  description = "WAF scope (REGIONAL or CLOUDFRONT)"
  type        = string
  default     = "REGIONAL"
}

# Rate Limiting
variable "rate_limit" {
  description = "Rate limit per 5 minutes per IP"
  type        = number
  default     = 2000
}

variable "rate_limit_action" {
  description = "Action when rate limit exceeded (block or count)"
  type        = string
  default     = "block"
}

# Managed Rules
variable "enable_common_rules" {
  description = "Enable AWS Common Rule Set"
  type        = bool
  default     = true
}

variable "enable_sqli_rules" {
  description = "Enable SQL injection rule set"
  type        = bool
  default     = true
}

variable "enable_xss_rules" {
  description = "Enable XSS rule set"
  type        = bool
  default     = true
}

variable "enable_known_bad_inputs" {
  description = "Enable Known Bad Inputs rule set"
  type        = bool
  default     = true
}

variable "enable_linux_rules" {
  description = "Enable Linux OS rule set"
  type        = bool
  default     = false
}

variable "enable_posix_rules" {
  description = "Enable POSIX OS rule set"
  type        = bool
  default     = false
}

variable "enable_ip_reputation" {
  description = "Enable IP reputation rule set"
  type        = bool
  default     = true
}

variable "enable_anonymous_ip" {
  description = "Enable Anonymous IP rule set"
  type        = bool
  default     = true
}

variable "enable_bot_control" {
  description = "Enable Bot Control rule set (additional cost)"
  type        = bool
  default     = false
}

# Geo Blocking
variable "enable_geo_blocking" {
  description = "Enable geo-blocking"
  type        = bool
  default     = false
}

variable "blocked_countries" {
  description = "List of country codes to block"
  type        = list(string)
  default     = []
}

variable "allowed_countries" {
  description = "List of country codes to allow (blocks all others if set)"
  type        = list(string)
  default     = []
}

# IP Allow/Block Lists
variable "allowed_ip_addresses" {
  description = "List of allowed IP addresses (CIDR)"
  type        = list(string)
  default     = []
}

variable "blocked_ip_addresses" {
  description = "List of blocked IP addresses (CIDR)"
  type        = list(string)
  default     = []
}

# Logging
variable "enable_logging" {
  description = "Enable WAF logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
