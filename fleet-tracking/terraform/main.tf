################################################################################
# GPS Tracking System - Main Terraform Configuration
################################################################################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  # Uncomment for remote state
  # backend "s3" {
  #   bucket         = "terraform-state-gps-tracking"
  #   key            = "kinesis/terraform.tfstate"
  #   region         = "eu-central-2"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

################################################################################
# Local Variables
################################################################################

locals {
  project_name = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Application = "gps-tracking"
  }
}

################################################################################
# Data Sources
################################################################################

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

################################################################################
# Kinesis Data Stream
################################################################################

module "kinesis" {
  source = "./modules/kinesis"

  project_name     = local.project_name
  stream_name      = "${local.project_name}-gps-coordinates"
  shard_count      = var.kinesis_shard_count
  retention_period = var.kinesis_retention_hours
  environment      = var.environment

  tags = local.common_tags
}

################################################################################
# DynamoDB Tables
################################################################################

module "dynamodb" {
  source = "./modules/dynamodb"

  project_name = local.project_name
  environment  = var.environment

  tags = local.common_tags
}

################################################################################
# S3 Bucket for Archive
################################################################################

module "s3" {
  source = "./modules/s3"

  project_name = local.project_name
  bucket_name  = "${local.project_name}-gps-archive-${data.aws_caller_identity.current.account_id}"
  environment  = var.environment

  tags = local.common_tags
}

################################################################################
# IAM Roles and Policies
################################################################################

module "iam" {
  source = "./modules/iam"

  project_name       = local.project_name
  kinesis_stream_arn = module.kinesis.stream_arn
  dynamodb_table_arns = [
    module.dynamodb.positions_table_arn,
    module.dynamodb.geofences_table_arn,
  ]
  s3_bucket_arn    = module.s3.bucket_arn
  sns_topic_arn    = module.sns.topic_arn
  environment      = var.environment

  tags = local.common_tags
}

################################################################################
# SNS Topic for Alerts
################################################################################

module "sns" {
  source = "./modules/sns"

  project_name = local.project_name
  topic_name   = "${local.project_name}-geofence-alerts"
  environment  = var.environment

  tags = local.common_tags
}

################################################################################
# Lambda Functions
################################################################################

module "lambda" {
  source = "./modules/lambda"

  project_name = local.project_name
  environment  = var.environment

  # Lambda configuration
  runtime     = "python3.12"
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  # IAM roles
  producer_role_arn           = module.iam.producer_role_arn
  dashboard_consumer_role_arn = module.iam.dashboard_consumer_role_arn
  geofence_consumer_role_arn  = module.iam.geofence_consumer_role_arn
  archive_consumer_role_arn   = module.iam.archive_consumer_role_arn

  # Resource ARNs for environment variables
  kinesis_stream_name    = module.kinesis.stream_name
  kinesis_stream_arn     = module.kinesis.stream_arn
  positions_table_name   = module.dynamodb.positions_table_name
  geofences_table_name   = module.dynamodb.geofences_table_name
  archive_bucket_name    = module.s3.bucket_name
  alerts_topic_arn       = module.sns.topic_arn

  # Consumer configuration
  consumer_batch_size          = var.consumer_batch_size
  consumer_parallelization     = var.consumer_parallelization
  consumer_starting_position   = var.consumer_starting_position
  max_batching_window_seconds  = var.max_batching_window_seconds

  tags = local.common_tags
}

################################################################################
# EventBridge Rule for Producer
################################################################################

module "eventbridge" {
  source = "./modules/eventbridge"

  project_name        = local.project_name
  producer_lambda_arn = module.lambda.producer_function_arn
  schedule_expression = var.producer_schedule
  environment         = var.environment

  tags = local.common_tags
}

################################################################################
# CloudWatch Monitoring
################################################################################

module "cloudwatch" {
  source = "./modules/cloudwatch"

  project_name       = local.project_name
  kinesis_stream_name = module.kinesis.stream_name
  lambda_function_names = [
    module.lambda.producer_function_name,
    module.lambda.dashboard_consumer_function_name,
    module.lambda.geofence_consumer_function_name,
    module.lambda.archive_consumer_function_name,
  ]
  environment = var.environment

  tags = local.common_tags
}
