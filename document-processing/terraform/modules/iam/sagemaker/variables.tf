variable "project_prefix" {
  type = string
}

variable "model_bucket_arn" {
  type = string
}

variable "processed_bucket_arn" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
