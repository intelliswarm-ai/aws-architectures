# =============================================================================
# Lambda Module - VPC-Enabled Lambda with Enterprise Features
# =============================================================================

locals {
  function_name = "${var.project_name}-${var.environment}-${var.function_name}"
  role_name     = "${local.function_name}-role"

  common_tags = merge(var.tags, {
    Module      = "lambda"
    Function    = var.function_name
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# IAM Role for Lambda
# -----------------------------------------------------------------------------
resource "aws_iam_role" "lambda" {
  count = var.create_role ? 1 : 0

  name = local.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

# Basic execution policy (CloudWatch Logs)
resource "aws_iam_role_policy_attachment" "basic_execution" {
  count = var.create_role ? 1 : 0

  role       = aws_iam_role.lambda[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# VPC execution policy (if VPC enabled)
resource "aws_iam_role_policy_attachment" "vpc_execution" {
  count = var.create_role && var.vpc_enabled ? 1 : 0

  role       = aws_iam_role.lambda[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# X-Ray tracing policy
resource "aws_iam_role_policy_attachment" "xray" {
  count = var.create_role && var.tracing_mode == "Active" ? 1 : 0

  role       = aws_iam_role.lambda[0].name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# Additional managed policies
resource "aws_iam_role_policy_attachment" "additional" {
  count = var.create_role ? length(var.additional_policies) : 0

  role       = aws_iam_role.lambda[0].name
  policy_arn = var.additional_policies[count.index]
}

# Inline policy
resource "aws_iam_role_policy" "inline" {
  count = var.create_role && var.inline_policy != null ? 1 : 0

  name   = "${local.function_name}-inline-policy"
  role   = aws_iam_role.lambda[0].id
  policy = var.inline_policy
}

# KMS policy for environment variable decryption
resource "aws_iam_role_policy" "kms" {
  count = var.create_role && var.kms_key_arn != null ? 1 : 0

  name = "${local.function_name}-kms-policy"
  role = aws_iam_role.lambda[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*"
        ]
        Resource = var.kms_key_arn
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# CloudWatch Log Group
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Lambda Function
# -----------------------------------------------------------------------------
resource "aws_lambda_function" "this" {
  function_name = local.function_name
  role          = var.create_role ? aws_iam_role.lambda[0].arn : var.role_arn
  handler       = var.handler
  runtime       = var.runtime
  memory_size   = var.memory_size
  timeout       = var.timeout

  filename         = var.source_path
  source_code_hash = filebase64sha256(var.source_path)

  layers = var.layers

  reserved_concurrent_executions = var.reserved_concurrent_executions

  environment {
    variables = merge(
      {
        ENVIRONMENT  = var.environment
        PROJECT_NAME = var.project_name
      },
      var.environment_variables
    )
  }

  # VPC Configuration
  dynamic "vpc_config" {
    for_each = var.vpc_enabled ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = var.security_group_ids
    }
  }

  # Dead Letter Queue
  dynamic "dead_letter_config" {
    for_each = var.dead_letter_target_arn != null ? [1] : []
    content {
      target_arn = var.dead_letter_target_arn
    }
  }

  # X-Ray Tracing
  tracing_config {
    mode = var.tracing_mode
  }

  # KMS for environment variables
  kms_key_arn = var.kms_key_arn

  depends_on = [aws_cloudwatch_log_group.lambda]

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Lambda Permissions (for various triggers)
# -----------------------------------------------------------------------------
resource "aws_lambda_permission" "allow_cloudwatch" {
  count = var.dead_letter_target_arn != null ? 0 : 0  # Placeholder for event triggers

  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
}
