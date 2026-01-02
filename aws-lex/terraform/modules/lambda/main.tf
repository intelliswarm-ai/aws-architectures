variable "name_prefix" {
  type = string
}

variable "environment" {
  type = string
}

variable "lambda_role_arn" {
  type = string
}

variable "bookings_table_name" {
  type = string
}

variable "flights_table_name" {
  type = string
}

variable "checkins_table_name" {
  type = string
}

variable "memory_size" {
  type    = number
  default = 256
}

variable "timeout" {
  type    = number
  default = 30
}

data "aws_region" "current" {}

# Lambda function for Lex fulfillment
resource "aws_lambda_function" "fulfillment" {
  function_name = "${var.name_prefix}-fulfillment"
  role          = var.lambda_role_arn
  handler       = "src.handlers.fulfillment_handler.handler"
  runtime       = "python3.12"
  memory_size   = var.memory_size
  timeout       = var.timeout

  filename         = "${path.module}/dummy.zip"
  source_code_hash = filebase64sha256("${path.module}/dummy.zip")

  environment {
    variables = {
      ENVIRONMENT      = var.environment
      BOOKINGS_TABLE   = var.bookings_table_name
      FLIGHTS_TABLE    = var.flights_table_name
      CHECKINS_TABLE   = var.checkins_table_name
      LOG_LEVEL        = var.environment == "prod" ? "INFO" : "DEBUG"
      POWERTOOLS_SERVICE_NAME = "airline-chatbot"
      POWERTOOLS_METRICS_NAMESPACE = "AirlineChatbot"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = {
    Name = "${var.name_prefix}-fulfillment"
  }

  lifecycle {
    ignore_changes = [
      filename,
      source_code_hash,
    ]
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "fulfillment" {
  name              = "/aws/lambda/${aws_lambda_function.fulfillment.function_name}"
  retention_in_days = var.environment == "prod" ? 90 : 30
}

# Lambda permission for Lex
resource "aws_lambda_permission" "lex_permission" {
  statement_id  = "AllowLexInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fulfillment.function_name
  principal     = "lexv2.amazonaws.com"
  source_arn    = "arn:aws:lex:${data.aws_region.current.name}:*:bot-alias/*"
}

# Dummy zip file for initial deployment
resource "local_file" "dummy_lambda" {
  filename = "${path.module}/dummy.zip"
  content  = ""

  lifecycle {
    ignore_changes = all
  }
}

output "fulfillment_lambda_arn" {
  value = aws_lambda_function.fulfillment.arn
}

output "fulfillment_lambda_name" {
  value = aws_lambda_function.fulfillment.function_name
}
