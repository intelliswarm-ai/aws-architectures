# GPS Tracking System - Default Configuration

aws_region   = "eu-central-2"
project_name = "gps-tracking"
environment  = "dev"

# Kinesis Configuration
kinesis_shard_count     = 4
kinesis_retention_hours = 24

# Lambda Configuration
lambda_memory_size = 256
lambda_timeout     = 60

# Consumer Configuration
consumer_batch_size          = 100
consumer_parallelization     = 2
consumer_starting_position   = "LATEST"
max_batching_window_seconds  = 5

# Producer Configuration
producer_schedule = "rate(1 minute)"
num_trucks        = 50
