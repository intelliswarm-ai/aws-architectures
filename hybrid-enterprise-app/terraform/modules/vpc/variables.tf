variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "enable_vpn_gateway" {
  description = "Enable VPN Gateway"
  type        = bool
  default     = false
}

variable "customer_gateway_ip" {
  description = "Customer gateway IP"
  type        = string
  default     = ""
}

variable "on_premises_cidr" {
  description = "On-premises CIDR"
  type        = string
  default     = "192.168.0.0/16"
}
