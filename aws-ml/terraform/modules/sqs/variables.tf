variable "project_prefix" {
  type = string
}

variable "visibility_timeout" {
  type    = number
  default = 120
}

variable "message_retention" {
  type    = number
  default = 1209600
}

variable "max_receive_count" {
  type    = number
  default = 3
}

variable "tags" {
  type    = map(string)
  default = {}
}
