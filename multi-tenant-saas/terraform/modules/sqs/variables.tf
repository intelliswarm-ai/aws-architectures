variable "name_prefix" {
  type = string
}

variable "visibility_timeout" {
  type    = number
  default = 60
}

variable "message_retention" {
  type    = number
  default = 1209600
}

variable "max_receive_count" {
  type    = number
  default = 3
}

variable "enable_encryption" {
  type    = bool
  default = false
}

variable "kms_key_id" {
  type    = string
  default = null
}

variable "tags" {
  type    = map(string)
  default = {}
}
