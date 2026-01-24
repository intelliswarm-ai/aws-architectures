# Terraform variable values for ML Canary Deployment

aws_region   = "eu-central-1"
environment  = "dev"
project_name = "ml-canary-deployment"

# SageMaker Configuration
sagemaker_instance_type          = "ml.m5.xlarge"
sagemaker_initial_instance_count = 1

# Auto-scaling Configuration
enable_auto_scaling            = true
autoscaling_min_capacity       = 1
autoscaling_max_capacity       = 10
autoscaling_target_invocations = 1000

# Monitoring Thresholds
latency_threshold_ms   = 100
error_rate_threshold   = 0.01
enable_auto_rollback   = true

# Lambda Configuration
lambda_memory_size = 512
lambda_timeout     = 60

# Logging
log_level = "INFO"

# Notifications (uncomment and set your email)
# alert_email = "your-email@example.com"
