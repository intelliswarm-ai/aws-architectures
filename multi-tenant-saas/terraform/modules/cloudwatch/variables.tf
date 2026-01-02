variable "name_prefix" {
  type = string
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "alarm_sns_topic_arns" {
  type    = list(string)
  default = []
}

variable "tags" {
  type    = map(string)
  default = {}
}
