variable "project_prefix" {
  type = string
}

variable "notification_email" {
  type    = string
  default = ""
}

variable "enable_email_notifications" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
