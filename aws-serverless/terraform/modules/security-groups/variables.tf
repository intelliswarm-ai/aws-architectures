variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "create_database_sg" {
  description = "Create database security group"
  type        = bool
  default     = false
}

variable "database_port" {
  description = "Database port"
  type        = number
  default     = 5432
}

variable "create_cache_sg" {
  description = "Create cache security group"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
