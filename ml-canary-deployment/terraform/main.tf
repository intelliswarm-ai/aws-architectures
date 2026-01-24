# ML Canary Deployment - Main Terraform Configuration
# This configuration deploys infrastructure for SageMaker model deployment
# with traffic splitting, A/B testing, and canary release capabilities.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

# Local variables
locals {
  project_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  # Lambda environment variables
  lambda_env_vars = {
    AWS_REGION                   = var.aws_region
    ENVIRONMENT                  = var.environment
    SAGEMAKER_ENDPOINT_NAME      = module.sagemaker.endpoint_name
    SAGEMAKER_MODEL_BUCKET       = module.s3.model_bucket_name
    SAGEMAKER_EXECUTION_ROLE_ARN = module.iam.sagemaker_execution_role_arn
    DEPLOYMENTS_TABLE            = module.dynamodb.deployments_table_name
    METRICS_TABLE                = module.dynamodb.metrics_table_name
    EVENTS_TABLE                 = module.dynamodb.events_table_name
    MODEL_ARTIFACTS_BUCKET       = module.s3.model_bucket_name
    INFERENCE_LOGS_BUCKET        = module.s3.logs_bucket_name
    ALERTS_TOPIC_ARN             = module.sns.alerts_topic_arn
    DEPLOYMENT_EVENTS_TOPIC_ARN  = module.sns.events_topic_arn
    LATENCY_THRESHOLD_MS         = tostring(var.latency_threshold_ms)
    ERROR_RATE_THRESHOLD         = tostring(var.error_rate_threshold)
    ENABLE_AUTO_ROLLBACK         = tostring(var.enable_auto_rollback)
    ENABLE_AUTO_SCALING          = tostring(var.enable_auto_scaling)
    LOG_LEVEL                    = var.log_level
  }
}

# S3 Module - Model artifacts and logs storage
module "s3" {
  source = "./modules/s3"

  project_prefix = local.project_prefix
  tags           = local.common_tags
}

# DynamoDB Module - Deployment state and metrics storage
module "dynamodb" {
  source = "./modules/dynamodb"

  project_prefix = local.project_prefix
  tags           = local.common_tags
}

# IAM Module - Roles and policies
module "iam" {
  source = "./modules/iam"

  project_prefix       = local.project_prefix
  model_bucket_arn     = module.s3.model_bucket_arn
  logs_bucket_arn      = module.s3.logs_bucket_arn
  deployments_table_arn = module.dynamodb.deployments_table_arn
  metrics_table_arn    = module.dynamodb.metrics_table_arn
  events_table_arn     = module.dynamodb.events_table_arn
  alerts_topic_arn     = module.sns.alerts_topic_arn
  events_topic_arn     = module.sns.events_topic_arn
  tags                 = local.common_tags
}

# SNS Module - Notifications
module "sns" {
  source = "./modules/sns"

  project_prefix    = local.project_prefix
  alert_email       = var.alert_email
  tags              = local.common_tags
}

# SageMaker Module - Endpoint configuration
module "sagemaker" {
  source = "./modules/sagemaker"

  project_prefix        = local.project_prefix
  execution_role_arn    = module.iam.sagemaker_execution_role_arn
  model_bucket_name     = module.s3.model_bucket_name
  initial_model_data    = var.initial_model_data
  instance_type         = var.sagemaker_instance_type
  initial_instance_count = var.sagemaker_initial_instance_count
  enable_auto_scaling   = var.enable_auto_scaling
  min_capacity          = var.autoscaling_min_capacity
  max_capacity          = var.autoscaling_max_capacity
  target_invocations    = var.autoscaling_target_invocations
  tags                  = local.common_tags
}

# Lambda Module - Handler functions
module "lambda" {
  source = "./modules/lambda"

  project_prefix        = local.project_prefix
  lambda_role_arn       = module.iam.lambda_execution_role_arn
  environment_variables = local.lambda_env_vars
  source_path           = var.lambda_source_path
  memory_size           = var.lambda_memory_size
  timeout               = var.lambda_timeout
  tags                  = local.common_tags
}

# API Gateway Module - REST API for inference
module "api_gateway" {
  source = "./modules/api-gateway"

  project_prefix            = local.project_prefix
  inference_lambda_arn      = module.lambda.api_handler_arn
  inference_lambda_name     = module.lambda.api_handler_name
  deployment_lambda_arn     = module.lambda.deployment_handler_arn
  deployment_lambda_name    = module.lambda.deployment_handler_name
  traffic_shift_lambda_arn  = module.lambda.traffic_shift_handler_arn
  traffic_shift_lambda_name = module.lambda.traffic_shift_handler_name
  rollback_lambda_arn       = module.lambda.rollback_handler_arn
  rollback_lambda_name      = module.lambda.rollback_handler_name
  stage_name                = var.environment
  tags                      = local.common_tags
}

# CloudWatch Module - Monitoring and alarms
module "cloudwatch" {
  source = "./modules/cloudwatch"

  project_prefix         = local.project_prefix
  endpoint_name          = module.sagemaker.endpoint_name
  latency_threshold_ms   = var.latency_threshold_ms
  error_rate_threshold   = var.error_rate_threshold
  alerts_topic_arn       = module.sns.alerts_topic_arn
  monitoring_lambda_arn  = module.lambda.monitoring_handler_arn
  monitoring_lambda_name = module.lambda.monitoring_handler_name
  tags                   = local.common_tags
}
