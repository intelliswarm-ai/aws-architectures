variable "project_prefix" {
  type = string
}

variable "raw_bucket_name" {
  type    = string
  default = ""
}

variable "processed_bucket_name" {
  type    = string
  default = ""
}

variable "model_bucket_name" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
