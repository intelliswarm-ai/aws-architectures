# Banking Platform - Terraform Variables

project_name = "banking-sqs"
environment  = "dev"
aws_region   = "eu-central-2"

# VPC Configuration
vpc_cidr             = "10.0.0.0/16"
enable_nat_gateway   = true
enable_vpc_endpoints = true

# SQS Configuration
sqs_visibility_timeout        = 60
sqs_message_retention_seconds = 1209600  # 14 days
sqs_max_receive_count         = 3

# EC2 Auto Scaling Configuration
ec2_instance_type            = "t3.medium"
asg_min_size                 = 2
asg_max_size                 = 10
asg_desired_capacity         = 2
target_messages_per_instance = 100

# Monitoring Configuration
log_retention_days          = 30
log_level                   = "INFO"
alarm_queue_depth_threshold = 1000
