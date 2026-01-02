# =============================================================================
# VPC Endpoints Module - Private AWS Service Access
# =============================================================================

locals {
  prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Module      = "vpc-endpoints"
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# Gateway Endpoints (Free)
# -----------------------------------------------------------------------------
# S3 Gateway Endpoint
resource "aws_vpc_endpoint" "s3" {
  count = var.enable_s3_endpoint ? 1 : 0

  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = var.route_table_ids

  tags = merge(local.common_tags, {
    Name = "${local.prefix}-s3-endpoint"
  })
}

# DynamoDB Gateway Endpoint
resource "aws_vpc_endpoint" "dynamodb" {
  count = var.enable_dynamodb_endpoint ? 1 : 0

  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = var.route_table_ids

  tags = merge(local.common_tags, {
    Name = "${local.prefix}-dynamodb-endpoint"
  })
}

# -----------------------------------------------------------------------------
# Interface Endpoints (Charged per hour + data)
# -----------------------------------------------------------------------------
# Secrets Manager
resource "aws_vpc_endpoint" "secretsmanager" {
  count = var.enable_secrets_manager_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [var.security_group_id]
  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.prefix}-secretsmanager-endpoint"
  })
}

# SSM (Parameter Store)
resource "aws_vpc_endpoint" "ssm" {
  count = var.enable_ssm_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.ssm"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [var.security_group_id]
  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.prefix}-ssm-endpoint"
  })
}

# SQS
resource "aws_vpc_endpoint" "sqs" {
  count = var.enable_sqs_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.sqs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [var.security_group_id]
  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.prefix}-sqs-endpoint"
  })
}

# SNS
resource "aws_vpc_endpoint" "sns" {
  count = var.enable_sns_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.sns"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [var.security_group_id]
  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.prefix}-sns-endpoint"
  })
}

# KMS
resource "aws_vpc_endpoint" "kms" {
  count = var.enable_kms_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.kms"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [var.security_group_id]
  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.prefix}-kms-endpoint"
  })
}

# CloudWatch Logs
resource "aws_vpc_endpoint" "logs" {
  count = var.enable_logs_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [var.security_group_id]
  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.prefix}-logs-endpoint"
  })
}

# EventBridge
resource "aws_vpc_endpoint" "events" {
  count = var.enable_events_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.events"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [var.security_group_id]
  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.prefix}-events-endpoint"
  })
}

# Bedrock Runtime (for GenAI)
resource "aws_vpc_endpoint" "bedrock" {
  count = var.enable_bedrock_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [var.security_group_id]
  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.prefix}-bedrock-endpoint"
  })
}

# API Gateway Execute API (for private APIs)
resource "aws_vpc_endpoint" "execute_api" {
  count = var.enable_execute_api_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.execute-api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [var.security_group_id]
  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.prefix}-execute-api-endpoint"
  })
}
