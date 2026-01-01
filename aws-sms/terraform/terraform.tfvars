# SMS Marketing System - Terraform Variables

aws_region   = "eu-central-2"
project_name = "sms-marketing"
environment  = "dev"

# Kinesis Configuration - 365 days retention for compliance
kinesis_shard_count      = 2
kinesis_retention_hours  = 8760  # 365 days

# Lambda Configuration
lambda_memory_size = 256
lambda_timeout     = 60

# Consumer Configuration
consumer_batch_size          = 100
consumer_parallelization     = 2
consumer_starting_position   = "LATEST"
max_batching_window_seconds  = 5

# Pinpoint Configuration
sms_sender_id    = "MARKETING"
sms_message_type = "PROMOTIONAL"
