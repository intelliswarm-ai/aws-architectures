# Environment Configuration
project_name = "secure-ml-transform"
environment  = "dev"
aws_region   = "eu-central-2"  # Zurich

# Network Configuration
vpc_cidr             = "10.0.0.0/16"
private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
availability_zones   = ["eu-central-2a", "eu-central-2b"]

# Glue Configuration
glue_worker_type       = "G.1X"
glue_number_of_workers = 10
glue_job_timeout       = 120

# Logging Configuration
log_retention_days = 90

# Transformation Configuration
pii_columns           = "customer_id,account_number,card_number,email,phone"
binning_method        = "percentile"
anomaly_contamination = 0.01
