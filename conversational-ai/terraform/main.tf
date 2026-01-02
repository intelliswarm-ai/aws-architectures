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
    tags = {
      Project     = "aws-lex-airline-chatbot"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

locals {
  name_prefix = "airline-${var.environment}"
}

# IAM roles and policies
module "iam" {
  source = "./modules/iam"

  name_prefix = local.name_prefix
  environment = var.environment
}

# DynamoDB tables
module "dynamodb" {
  source = "./modules/dynamodb"

  name_prefix = local.name_prefix
  environment = var.environment
}

# Lambda functions
module "lambda" {
  source = "./modules/lambda"

  name_prefix         = local.name_prefix
  environment         = var.environment
  lambda_role_arn     = module.iam.lambda_role_arn
  bookings_table_name = module.dynamodb.bookings_table_name
  flights_table_name  = module.dynamodb.flights_table_name
  checkins_table_name = module.dynamodb.checkins_table_name

  depends_on = [module.iam, module.dynamodb]
}

# Lex bot
module "lex" {
  source = "./modules/lex"

  name_prefix              = local.name_prefix
  environment              = var.environment
  bot_locale               = var.bot_locale
  fulfillment_lambda_arn   = module.lambda.fulfillment_lambda_arn
  lex_role_arn             = module.iam.lex_role_arn
  idle_session_ttl_seconds = var.idle_timeout

  depends_on = [module.lambda]
}

# CloudWatch monitoring
module "cloudwatch" {
  source = "./modules/cloudwatch"

  name_prefix              = local.name_prefix
  environment              = var.environment
  fulfillment_lambda_name  = module.lambda.fulfillment_lambda_name
  lex_bot_id               = module.lex.bot_id

  depends_on = [module.lex, module.lambda]
}

# Optional API Gateway for programmatic access
module "api_gateway" {
  source = "./modules/api_gateway"

  name_prefix         = local.name_prefix
  environment         = var.environment
  lex_bot_id          = module.lex.bot_id
  lex_bot_alias_id    = module.lex.bot_alias_id
  api_gateway_role_arn = module.iam.api_gateway_role_arn

  depends_on = [module.lex]
}
