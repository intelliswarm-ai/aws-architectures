variable "project_prefix" {
  type = string
}

variable "model_bucket_name" {
  type = string
}

variable "role_arn" {
  type = string
}

variable "instance_type" {
  type    = string
  default = "ml.m5.large"
}

variable "instance_count" {
  type    = number
  default = 1
}

variable "tags" {
  type    = map(string)
  default = {}
}
