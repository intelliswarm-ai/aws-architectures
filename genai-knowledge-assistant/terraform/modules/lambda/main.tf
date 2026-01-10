# =============================================================================
# Lambda Module - Functions
# =============================================================================

locals {
  lambda_source_path = "${path.root}/../dist/lambda.zip"
}

# =============================================================================
# API Handler
# =============================================================================

resource "aws_lambda_function" "api_handler" {
  function_name = "${var.project_prefix}-api-handler"
  role          = var.lambda_role_arn
  handler       = "src.handlers.api_handler.handler"
  runtime       = "python3.12"
  timeout       = var.timeout
  memory_size   = var.memory_size

  filename         = local.lambda_source_path
  source_code_hash = fileexists(local.lambda_source_path) ? filebase64sha256(local.lambda_source_path) : null

  environment {
    variables = var.environment_variables
  }

  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "api_handler" {
  name              = "/aws/lambda/${aws_lambda_function.api_handler.function_name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

# =============================================================================
# Query Handler
# =============================================================================

resource "aws_lambda_function" "query_handler" {
  function_name = "${var.project_prefix}-query-handler"
  role          = var.lambda_role_arn
  handler       = "src.handlers.query_handler.handler"
  runtime       = "python3.12"
  timeout       = 120  # Longer timeout for RAG queries
  memory_size   = var.memory_size

  filename         = local.lambda_source_path
  source_code_hash = fileexists(local.lambda_source_path) ? filebase64sha256(local.lambda_source_path) : null

  environment {
    variables = var.environment_variables
  }

  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "query_handler" {
  name              = "/aws/lambda/${aws_lambda_function.query_handler.function_name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

# =============================================================================
# Ingestion Handler
# =============================================================================

resource "aws_lambda_function" "ingestion_handler" {
  function_name = "${var.project_prefix}-ingestion-handler"
  role          = var.lambda_role_arn
  handler       = "src.handlers.ingestion_handler.handler"
  runtime       = "python3.12"
  timeout       = 300  # Longer timeout for document processing
  memory_size   = 1024  # More memory for embedding generation

  filename         = local.lambda_source_path
  source_code_hash = fileexists(local.lambda_source_path) ? filebase64sha256(local.lambda_source_path) : null

  environment {
    variables = var.environment_variables
  }

  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "ingestion_handler" {
  name              = "/aws/lambda/${aws_lambda_function.ingestion_handler.function_name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

# S3 trigger permission
resource "aws_lambda_permission" "ingestion_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion_handler.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.documents_bucket_arn
}

# =============================================================================
# Agent Handler
# =============================================================================

resource "aws_lambda_function" "agent_handler" {
  function_name = "${var.project_prefix}-agent-handler"
  role          = var.lambda_role_arn
  handler       = "src.handlers.agent_handler.handler"
  runtime       = "python3.12"
  timeout       = 120
  memory_size   = var.memory_size

  filename         = local.lambda_source_path
  source_code_hash = fileexists(local.lambda_source_path) ? filebase64sha256(local.lambda_source_path) : null

  environment {
    variables = var.environment_variables
  }

  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "agent_handler" {
  name              = "/aws/lambda/${aws_lambda_function.agent_handler.function_name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

# =============================================================================
# Sync Handler
# =============================================================================

resource "aws_lambda_function" "sync_handler" {
  function_name = "${var.project_prefix}-sync-handler"
  role          = var.lambda_role_arn
  handler       = "src.handlers.sync_handler.handler"
  runtime       = "python3.12"
  timeout       = 60
  memory_size   = 256

  filename         = local.lambda_source_path
  source_code_hash = fileexists(local.lambda_source_path) ? filebase64sha256(local.lambda_source_path) : null

  environment {
    variables = var.environment_variables
  }

  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "sync_handler" {
  name              = "/aws/lambda/${aws_lambda_function.sync_handler.function_name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

# EventBridge permission for scheduled sync
resource "aws_lambda_permission" "sync_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sync_handler.function_name
  principal     = "events.amazonaws.com"
}

# =============================================================================
# Scheduled Sync Rule (Optional - Daily Sync)
# =============================================================================

resource "aws_cloudwatch_event_rule" "daily_sync" {
  name                = "${var.project_prefix}-daily-sync"
  description         = "Trigger daily knowledge base sync"
  schedule_expression = "rate(1 day)"
  is_enabled          = false  # Enable manually when ready

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "daily_sync" {
  rule      = aws_cloudwatch_event_rule.daily_sync.name
  target_id = "sync-handler"
  arn       = aws_lambda_function.sync_handler.arn
}
