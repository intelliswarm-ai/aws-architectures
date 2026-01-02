################################################################################
# Banking Platform - Main Terraform Configuration
# EC2 Auto Scaling with SQS-based Scaling
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
  #   bucket         = "terraform-state-banking"
  #   key            = "sqs/terraform.tfstate"
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
    Application = "banking-platform"
  }

  availability_zones = [
    "${var.aws_region}a",
    "${var.aws_region}b",
  ]
}

################################################################################
# Data Sources
################################################################################

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

################################################################################
# VPC Module
################################################################################

module "vpc" {
  source = "./modules/vpc"

  project_name         = local.project_name
  environment          = var.environment
  aws_region           = var.aws_region
  vpc_cidr             = var.vpc_cidr
  availability_zones   = local.availability_zones
  enable_nat_gateway   = var.enable_nat_gateway
  enable_vpc_endpoints = var.enable_vpc_endpoints

  tags = local.common_tags
}

################################################################################
# DynamoDB Tables
################################################################################

# Transactions Table
resource "aws_dynamodb_table" "transactions" {
  name         = "${local.project_name}-transactions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "transaction_id"

  attribute {
    name = "transaction_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-transactions"
  })
}

# Idempotency Table
resource "aws_dynamodb_table" "idempotency" {
  name         = "${local.project_name}-idempotency"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "idempotency_key"

  attribute {
    name = "idempotency_key"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-idempotency"
  })
}

# DLQ Records Table
resource "aws_dynamodb_table" "dlq_records" {
  name         = "${local.project_name}-dlq-records"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "message_id"

  attribute {
    name = "message_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-dlq-records"
  })
}

################################################################################
# S3 Module (must be created before IAM for bucket ARN)
################################################################################

module "s3" {
  source = "./modules/s3"

  project_name = local.project_name
  environment  = var.environment
  bucket_name  = "${local.project_name}-deployment-${data.aws_caller_identity.current.account_id}"
  ec2_role_arn = module.iam.ec2_role_arn

  tags = local.common_tags

  depends_on = [module.iam]
}

################################################################################
# IAM Module
################################################################################

module "iam" {
  source = "./modules/iam"

  project_name        = local.project_name
  environment         = var.environment
  sqs_queue_arn       = module.sqs.queue_arn
  sqs_dlq_arn         = module.sqs.dlq_arn
  dynamodb_table_arns = [
    aws_dynamodb_table.transactions.arn,
    aws_dynamodb_table.idempotency.arn,
    aws_dynamodb_table.dlq_records.arn,
  ]
  s3_bucket_arn = "arn:aws:s3:::${local.project_name}-deployment-${data.aws_caller_identity.current.account_id}"

  tags = local.common_tags

  depends_on = [module.sqs]
}

################################################################################
# SQS Module
################################################################################

module "sqs" {
  source = "./modules/sqs"

  project_name              = local.project_name
  environment               = var.environment
  aws_region                = var.aws_region
  account_id                = data.aws_caller_identity.current.account_id
  visibility_timeout        = var.sqs_visibility_timeout
  message_retention_seconds = var.sqs_message_retention_seconds
  max_receive_count         = var.sqs_max_receive_count
  ec2_role_arn              = module.iam.ec2_role_arn

  tags = local.common_tags

  depends_on = [module.iam]
}

################################################################################
# EC2 Auto Scaling Module
################################################################################

module "ec2" {
  source = "./modules/ec2"

  project_name                 = local.project_name
  environment                  = var.environment
  aws_region                   = var.aws_region
  vpc_id                       = module.vpc.vpc_id
  public_subnet_ids            = module.vpc.public_subnet_ids
  private_subnet_ids           = module.vpc.private_subnet_ids
  instance_type                = var.ec2_instance_type
  min_size                     = var.asg_min_size
  max_size                     = var.asg_max_size
  desired_capacity             = var.asg_desired_capacity
  target_messages_per_instance = var.target_messages_per_instance
  instance_profile_arn         = module.iam.ec2_instance_profile_arn
  transaction_queue_url        = module.sqs.queue_url
  transactions_table_name      = aws_dynamodb_table.transactions.name
  idempotency_table_name       = aws_dynamodb_table.idempotency.name
  s3_bucket                    = module.s3.bucket_name
  log_group_name               = module.cloudwatch.processor_log_group_name

  tags = local.common_tags

  depends_on = [
    module.vpc,
    module.iam,
    module.sqs,
    module.s3,
    module.cloudwatch,
  ]
}

################################################################################
# CloudWatch Module
################################################################################

module "cloudwatch" {
  source = "./modules/cloudwatch"

  project_name                 = local.project_name
  environment                  = var.environment
  aws_region                   = var.aws_region
  log_retention_days           = var.log_retention_days
  sqs_queue_name               = module.sqs.queue_name
  dlq_name                     = module.sqs.dlq_name
  asg_name                     = "${local.project_name}-processor-asg"
  lambda_function_names        = [
    "${local.project_name}-api",
    "${local.project_name}-metrics",
    "${local.project_name}-dlq-processor",
  ]
  target_messages_per_instance = var.target_messages_per_instance
  queue_depth_threshold        = var.alarm_queue_depth_threshold
  min_instances                = var.asg_min_size

  tags = local.common_tags

  depends_on = [module.sqs]
}

################################################################################
# Lambda Functions
################################################################################

# Lambda deployment package
data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../dist/package"
  output_path = "${path.module}/../dist/lambda.zip"
}

# API Handler Lambda
resource "aws_lambda_function" "api" {
  function_name = "${local.project_name}-api"
  role          = module.iam.lambda_role_arn
  handler       = "src.handlers.api_handler.handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 256

  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT              = var.environment
      TRANSACTION_QUEUE_URL    = module.sqs.queue_url
      TRANSACTIONS_TABLE_NAME  = aws_dynamodb_table.transactions.name
      IDEMPOTENCY_TABLE_NAME   = aws_dynamodb_table.idempotency.name
      LOG_LEVEL                = var.log_level
      POWERTOOLS_SERVICE_NAME  = "banking-api"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags

  depends_on = [module.cloudwatch]
}

# Metrics Handler Lambda
resource "aws_lambda_function" "metrics" {
  function_name = "${local.project_name}-metrics"
  role          = module.iam.lambda_role_arn
  handler       = "src.handlers.metrics_handler.handler"
  runtime       = "python3.12"
  timeout       = 60
  memory_size   = 256

  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT             = var.environment
      TRANSACTION_QUEUE_URL   = module.sqs.queue_url
      LOG_LEVEL               = var.log_level
      POWERTOOLS_SERVICE_NAME = "banking-metrics"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags

  depends_on = [module.cloudwatch]
}

# DLQ Handler Lambda
resource "aws_lambda_function" "dlq" {
  function_name = "${local.project_name}-dlq-processor"
  role          = module.iam.lambda_role_arn
  handler       = "src.handlers.dlq_handler.handler"
  runtime       = "python3.12"
  timeout       = 60
  memory_size   = 256

  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT             = var.environment
      DLQ_TABLE_NAME          = aws_dynamodb_table.dlq_records.name
      LOG_LEVEL               = var.log_level
      POWERTOOLS_SERVICE_NAME = "banking-dlq"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags

  depends_on = [module.cloudwatch]
}

# DLQ Lambda Event Source Mapping
resource "aws_lambda_event_source_mapping" "dlq" {
  event_source_arn = module.sqs.dlq_arn
  function_name    = aws_lambda_function.dlq.arn
  batch_size       = 10
  enabled          = true

  function_response_types = ["ReportBatchItemFailures"]
}

# EventBridge rule for metrics collection (every minute)
resource "aws_cloudwatch_event_rule" "metrics" {
  name                = "${local.project_name}-metrics-schedule"
  description         = "Trigger metrics collection every minute"
  schedule_expression = "rate(1 minute)"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "metrics" {
  rule      = aws_cloudwatch_event_rule.metrics.name
  target_id = "MetricsLambda"
  arn       = aws_lambda_function.metrics.arn
}

resource "aws_lambda_permission" "metrics" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.metrics.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.metrics.arn
}

################################################################################
# API Gateway
################################################################################

resource "aws_apigatewayv2_api" "main" {
  name          = "${local.project_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_origins = ["*"]
    max_age       = 300
  }

  tags = local.common_tags
}

resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
    })
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${local.project_name}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
