variable "function_name" {
  type = string
}

variable "description" {
  type    = string
  default = ""
}

variable "handler" {
  type = string
}

variable "runtime" {
  type    = string
  default = "python3.12"
}

variable "source_path" {
  type = string
}

variable "role_arn" {
  type = string
}

variable "memory_size" {
  type    = number
  default = 512
}

variable "timeout" {
  type    = number
  default = 60
}

variable "environment_variables" {
  type    = map(string)
  default = {}
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "enable_xray" {
  type    = bool
  default = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
