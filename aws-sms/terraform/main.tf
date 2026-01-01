################################################################################
# SMS Marketing System - Main Terraform Configuration
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
  #   bucket         = "terraform-state-sms-marketing"
  #   key            = "sms/terraform.tfstate"
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
    Application = "sms-marketing"
  }
}

################################################################################
# Data Sources
################################################################################

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

################################################################################
# Amazon Pinpoint Application
################################################################################

module "pinpoint" {
  source = "./modules/pinpoint"

  project_name        = local.project_name
  environment         = var.environment
  kinesis_stream_arn  = module.kinesis.stream_arn
  kinesis_role_arn    = module.iam.pinpoint_kinesis_role_arn

  tags = local.common_tags
}

################################################################################
# Kinesis Data Stream (365-day retention)
################################################################################

module "kinesis" {
  source = "./modules/kinesis"

  project_name     = local.project_name
  stream_name      = "${local.project_name}-sms-events"
  shard_count      = var.kinesis_shard_count
  retention_period = var.kinesis_retention_hours  # 8760 hours = 365 days
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
  bucket_name  = "${local.project_name}-sms-archive-${data.aws_caller_identity.current.account_id}"
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
    module.dynamodb.responses_table_arn,
    module.dynamodb.subscribers_table_arn,
  ]
  s3_bucket_arn      = module.s3.bucket_arn
  sns_topic_arn      = module.sns.topic_arn
  pinpoint_app_arn   = module.pinpoint.app_arn
  environment        = var.environment

  tags = local.common_tags
}

################################################################################
# SNS Topic for Notifications
################################################################################

module "sns" {
  source = "./modules/sns"

  project_name = local.project_name
  topic_name   = "${local.project_name}-sms-notifications"
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
  event_processor_role_arn     = module.iam.event_processor_role_arn
  response_handler_role_arn    = module.iam.response_handler_role_arn
  analytics_processor_role_arn = module.iam.analytics_processor_role_arn
  archive_consumer_role_arn    = module.iam.archive_consumer_role_arn

  # Resource ARNs for environment variables
  kinesis_stream_name    = module.kinesis.stream_name
  kinesis_stream_arn     = module.kinesis.stream_arn
  responses_table_name   = module.dynamodb.responses_table_name
  subscribers_table_name = module.dynamodb.subscribers_table_name
  archive_bucket_name    = module.s3.bucket_name
  notifications_topic_arn = module.sns.topic_arn
  pinpoint_app_id        = module.pinpoint.app_id

  # Consumer configuration
  consumer_batch_size          = var.consumer_batch_size
  consumer_parallelization     = var.consumer_parallelization
  consumer_starting_position   = var.consumer_starting_position
  max_batching_window_seconds  = var.max_batching_window_seconds

  tags = local.common_tags
}

################################################################################
# CloudWatch Monitoring
################################################################################

module "cloudwatch" {
  source = "./modules/cloudwatch"

  project_name        = local.project_name
  kinesis_stream_name = module.kinesis.stream_name
  pinpoint_app_id     = module.pinpoint.app_id
  lambda_function_names = [
    module.lambda.event_processor_function_name,
    module.lambda.response_handler_function_name,
    module.lambda.analytics_processor_function_name,
    module.lambda.archive_consumer_function_name,
  ]
  environment = var.environment

  tags = local.common_tags
}
