# =============================================================================
# AWS Budgets Module - Cost Management
# =============================================================================

locals {
  prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Module      = "budgets"
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# Overall Monthly Budget
# -----------------------------------------------------------------------------
resource "aws_budgets_budget" "monthly" {
  name         = "${local.prefix}-monthly-budget"
  budget_type  = "COST"
  limit_amount = var.budget_limit
  limit_unit   = "USD"
  time_unit    = var.budget_time_unit

  cost_filter {
    name   = "TagKeyValue"
    values = ["${var.cost_allocation_tag}$${var.project_name}"]
  }

  # 50% Actual
  dynamic "notification" {
    for_each = var.notification_threshold_50 && var.notification_email != "" ? [1] : []
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 50
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.notification_email]
    }
  }

  # 80% Actual
  dynamic "notification" {
    for_each = var.notification_threshold_80 && var.notification_email != "" ? [1] : []
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 80
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.notification_email]
    }
  }

  # 100% Actual
  dynamic "notification" {
    for_each = var.notification_threshold_100 && var.notification_email != "" ? [1] : []
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 100
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.notification_email]
    }
  }

  # Forecasted 100%
  dynamic "notification" {
    for_each = var.notification_threshold_forecast && var.notification_email != "" ? [1] : []
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 100
      threshold_type             = "PERCENTAGE"
      notification_type          = "FORECASTED"
      subscriber_email_addresses = [var.notification_email]
    }
  }

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Lambda Service Budget
# -----------------------------------------------------------------------------
resource "aws_budgets_budget" "lambda" {
  count = var.enable_lambda_budget ? 1 : 0

  name         = "${local.prefix}-lambda-budget"
  budget_type  = "COST"
  limit_amount = var.lambda_budget_limit
  limit_unit   = "USD"
  time_unit    = var.budget_time_unit

  cost_filter {
    name   = "Service"
    values = ["AWS Lambda"]
  }

  cost_filter {
    name   = "TagKeyValue"
    values = ["${var.cost_allocation_tag}$${var.project_name}"]
  }

  dynamic "notification" {
    for_each = var.notification_email != "" ? [1] : []
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 80
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.notification_email]
    }
  }

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# DynamoDB Service Budget
# -----------------------------------------------------------------------------
resource "aws_budgets_budget" "dynamodb" {
  count = var.enable_dynamodb_budget ? 1 : 0

  name         = "${local.prefix}-dynamodb-budget"
  budget_type  = "COST"
  limit_amount = var.dynamodb_budget_limit
  limit_unit   = "USD"
  time_unit    = var.budget_time_unit

  cost_filter {
    name   = "Service"
    values = ["Amazon DynamoDB"]
  }

  cost_filter {
    name   = "TagKeyValue"
    values = ["${var.cost_allocation_tag}$${var.project_name}"]
  }

  dynamic "notification" {
    for_each = var.notification_email != "" ? [1] : []
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 80
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.notification_email]
    }
  }

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# API Gateway Service Budget
# -----------------------------------------------------------------------------
resource "aws_budgets_budget" "api_gateway" {
  count = var.enable_api_gateway_budget ? 1 : 0

  name         = "${local.prefix}-apigateway-budget"
  budget_type  = "COST"
  limit_amount = var.api_gateway_budget_limit
  limit_unit   = "USD"
  time_unit    = var.budget_time_unit

  cost_filter {
    name   = "Service"
    values = ["Amazon API Gateway"]
  }

  cost_filter {
    name   = "TagKeyValue"
    values = ["${var.cost_allocation_tag}$${var.project_name}"]
  }

  dynamic "notification" {
    for_each = var.notification_email != "" ? [1] : []
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 80
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.notification_email]
    }
  }

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Cost Anomaly Detection
# -----------------------------------------------------------------------------
resource "aws_ce_anomaly_monitor" "this" {
  name              = "${local.prefix}-anomaly-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"

  tags = local.common_tags
}

resource "aws_ce_anomaly_subscription" "this" {
  count = var.notification_email != "" ? 1 : 0

  name      = "${local.prefix}-anomaly-subscription"
  frequency = "DAILY"

  monitor_arn_list = [aws_ce_anomaly_monitor.this.arn]

  subscriber {
    type    = "EMAIL"
    address = var.notification_email
  }

  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_PERCENTAGE"
      values        = ["10"]
      match_options = ["GREATER_THAN_OR_EQUAL"]
    }
  }

  tags = local.common_tags
}
