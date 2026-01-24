# Lambda Module - Handler functions

# API Handler
resource "aws_lambda_function" "api_handler" {
  function_name = "${var.project_prefix}-api-handler"
  role          = var.lambda_role_arn
  handler       = "src.handlers.api_handler.handler"
  runtime       = "python3.12"
  filename      = var.source_path
  memory_size   = var.memory_size
  timeout       = var.timeout

  environment {
    variables = var.environment_variables
  }

  tracing_config {
    mode = "Active"
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "api_handler" {
  name              = "/aws/lambda/${aws_lambda_function.api_handler.function_name}"
  retention_in_days = 14
}

# Deployment Handler
resource "aws_lambda_function" "deployment_handler" {
  function_name = "${var.project_prefix}-deployment-handler"
  role          = var.lambda_role_arn
  handler       = "src.handlers.deployment_handler.handler"
  runtime       = "python3.12"
  filename      = var.source_path
  memory_size   = var.memory_size
  timeout       = 300  # Longer timeout for deployment operations

  environment {
    variables = var.environment_variables
  }

  tracing_config {
    mode = "Active"
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "deployment_handler" {
  name              = "/aws/lambda/${aws_lambda_function.deployment_handler.function_name}"
  retention_in_days = 14
}

# Monitoring Handler
resource "aws_lambda_function" "monitoring_handler" {
  function_name = "${var.project_prefix}-monitoring-handler"
  role          = var.lambda_role_arn
  handler       = "src.handlers.monitoring_handler.handler"
  runtime       = "python3.12"
  filename      = var.source_path
  memory_size   = var.memory_size
  timeout       = var.timeout

  environment {
    variables = var.environment_variables
  }

  tracing_config {
    mode = "Active"
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "monitoring_handler" {
  name              = "/aws/lambda/${aws_lambda_function.monitoring_handler.function_name}"
  retention_in_days = 14
}

# Traffic Shift Handler
resource "aws_lambda_function" "traffic_shift_handler" {
  function_name = "${var.project_prefix}-traffic-shift-handler"
  role          = var.lambda_role_arn
  handler       = "src.handlers.traffic_shift_handler.handler"
  runtime       = "python3.12"
  filename      = var.source_path
  memory_size   = var.memory_size
  timeout       = var.timeout

  environment {
    variables = var.environment_variables
  }

  tracing_config {
    mode = "Active"
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "traffic_shift_handler" {
  name              = "/aws/lambda/${aws_lambda_function.traffic_shift_handler.function_name}"
  retention_in_days = 14
}

# Rollback Handler
resource "aws_lambda_function" "rollback_handler" {
  function_name = "${var.project_prefix}-rollback-handler"
  role          = var.lambda_role_arn
  handler       = "src.handlers.rollback_handler.handler"
  runtime       = "python3.12"
  filename      = var.source_path
  memory_size   = var.memory_size
  timeout       = var.timeout

  environment {
    variables = var.environment_variables
  }

  tracing_config {
    mode = "Active"
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "rollback_handler" {
  name              = "/aws/lambda/${aws_lambda_function.rollback_handler.function_name}"
  retention_in_days = 14
}
