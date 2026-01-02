variable "project_prefix" {
  type = string
}

variable "lambda_function_names" {
  type = list(string)
}

variable "workflow_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
