variable "table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "read_capacity" {
  description = "Read capacity units (for provisioned mode)"
  type        = number
  default     = 5
}

variable "write_capacity" {
  description = "Write capacity units (for provisioned mode)"
  type        = number
  default     = 5
}

variable "gsi_read_capacity" {
  description = "GSI read capacity units (for provisioned mode)"
  type        = number
  default     = 5
}

variable "gsi_write_capacity" {
  description = "GSI write capacity units (for provisioned mode)"
  type        = number
  default     = 5
}

variable "enable_ttl" {
  description = "Enable TTL on the table"
  type        = bool
  default     = true
}

variable "enable_pitr" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = false
}

variable "enable_autoscaling" {
  description = "Enable autoscaling (for provisioned mode)"
  type        = bool
  default     = false
}

variable "autoscaling_max_read_capacity" {
  description = "Maximum read capacity for autoscaling"
  type        = number
  default     = 100
}

variable "autoscaling_max_write_capacity" {
  description = "Maximum write capacity for autoscaling"
  type        = number
  default     = 100
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
