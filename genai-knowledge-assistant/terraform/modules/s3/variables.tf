variable "project_prefix" {
  description = "Project name prefix"
  type        = string
}

variable "documents_bucket_name" {
  description = "Custom bucket name (leave empty for auto-generated)"
  type        = string
  default     = ""
}

variable "enable_versioning" {
  description = "Enable bucket versioning"
  type        = bool
  default     = true
}

variable "enable_event_notifications" {
  description = "Enable S3 event notifications"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
