################################################################################
# Input Variables
################################################################################

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "banking-sqs"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-2"
}

################################################################################
# VPC Configuration
################################################################################

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for AWS services"
  type        = bool
  default     = true
}

################################################################################
# SQS Configuration
################################################################################

variable "sqs_visibility_timeout" {
  description = "Visibility timeout for SQS messages (seconds)"
  type        = number
  default     = 60
}

variable "sqs_message_retention_seconds" {
  description = "Message retention period (seconds)"
  type        = number
  default     = 1209600  # 14 days
}

variable "sqs_max_receive_count" {
  description = "Maximum receives before sending to DLQ"
  type        = number
  default     = 3
}

################################################################################
# EC2 Auto Scaling Configuration
################################################################################

variable "ec2_instance_type" {
  description = "EC2 instance type for processors"
  type        = string
  default     = "t3.medium"
}

variable "asg_min_size" {
  description = "Minimum number of instances in ASG"
  type        = number
  default     = 2
}

variable "asg_max_size" {
  description = "Maximum number of instances in ASG"
  type        = number
  default     = 10
}

variable "asg_desired_capacity" {
  description = "Desired number of instances in ASG"
  type        = number
  default     = 2
}

variable "target_messages_per_instance" {
  description = "Target number of messages per instance for scaling"
  type        = number
  default     = 100
}

################################################################################
# Monitoring Configuration
################################################################################

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
}

variable "alarm_queue_depth_threshold" {
  description = "Queue depth threshold for alarm"
  type        = number
  default     = 1000
}
