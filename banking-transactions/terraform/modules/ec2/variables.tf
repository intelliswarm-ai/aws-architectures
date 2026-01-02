################################################################################
# EC2 Module Variables
################################################################################

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for ALB"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for EC2 instances"
  type        = list(string)
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "min_size" {
  description = "Minimum number of instances in ASG"
  type        = number
  default     = 2
}

variable "max_size" {
  description = "Maximum number of instances in ASG"
  type        = number
  default     = 10
}

variable "desired_capacity" {
  description = "Desired number of instances in ASG"
  type        = number
  default     = 2
}

variable "target_messages_per_instance" {
  description = "Target number of messages per instance for scaling"
  type        = number
  default     = 100
}

variable "instance_profile_arn" {
  description = "ARN of the IAM instance profile"
  type        = string
}

variable "transaction_queue_url" {
  description = "URL of the SQS transaction queue"
  type        = string
}

variable "transactions_table_name" {
  description = "Name of the transactions DynamoDB table"
  type        = string
}

variable "idempotency_table_name" {
  description = "Name of the idempotency DynamoDB table"
  type        = string
}

variable "s3_bucket" {
  description = "S3 bucket for application deployment"
  type        = string
}

variable "log_group_name" {
  description = "CloudWatch log group name"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
