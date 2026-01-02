# ============================================
# Variables
# ============================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-2"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "application_name" {
  description = "Application name"
  type        = string
  default     = "inventory-management"
}

# ============================================
# VPC Configuration
# ============================================

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "enable_vpn_gateway" {
  description = "Enable VPN Gateway for on-premises connectivity"
  type        = bool
  default     = true
}

variable "customer_gateway_ip" {
  description = "Customer gateway public IP address (on-premises VPN endpoint)"
  type        = string
  default     = ""
}

variable "on_premises_cidr" {
  description = "On-premises network CIDR block"
  type        = string
  default     = "192.168.0.0/16"
}

# ============================================
# Elastic Beanstalk Configuration
# ============================================

variable "solution_stack_name" {
  description = "Elastic Beanstalk solution stack"
  type        = string
  default     = "64bit Amazon Linux 2023 v4.2.1 running Corretto 21"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 4
}

# ============================================
# Database Configuration (On-Premises Oracle)
# ============================================

variable "database_url" {
  description = "Oracle database JDBC URL"
  type        = string
  sensitive   = true
}

variable "database_username" {
  description = "Database username"
  type        = string
  sensitive   = true
}

variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# ============================================
# Monitoring
# ============================================

variable "alarm_email" {
  description = "Email for CloudWatch alarms"
  type        = string
  default     = ""
}
