variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "on_premises_cidr" {
  description = "On-premises CIDR for Oracle access"
  type        = string
}
