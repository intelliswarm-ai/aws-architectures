variable "project_prefix" {
  type = string
}

variable "inference_lambda_arn" {
  type = string
}

variable "inference_lambda_name" {
  type = string
}

variable "bedrock_lambda_arn" {
  type = string
}

variable "bedrock_lambda_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
