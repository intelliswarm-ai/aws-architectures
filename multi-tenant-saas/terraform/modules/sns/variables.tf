variable "name_prefix" {
  type = string
}

variable "enable_encryption" {
  type    = bool
  default = false
}

variable "kms_key_id" {
  type    = string
  default = null
}

variable "notification_email" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
