variable "environment" {
  type = string
}

variable "name_prefix" {
  type = string
}

variable "lambda_execution_role_arn" {
  type = string
}

variable "transcripts_bucket" {
  type = string
}

variable "output_bucket" {
  type = string
}

variable "opensearch_endpoint" {
  type = string
}

variable "comprehend_role_arn" {
  type = string
}

variable "log_retention_days" {
  type    = number
  default = 30
}

data "aws_region" "current" {}

locals {
  runtime     = "python3.12"
  timeout     = 300
  memory_size = 512

  common_env_vars = {
    POWERTOOLS_SERVICE_NAME = "call-sentiment"
    LOG_LEVEL               = var.environment == "prod" ? "INFO" : "DEBUG"
    AWS_REGION              = data.aws_region.current.name
    TRANSCRIPTS_BUCKET      = var.transcripts_bucket
    OUTPUT_BUCKET           = var.output_bucket
    OPENSEARCH_ENDPOINT     = var.opensearch_endpoint
    COMPREHEND_ROLE_ARN     = var.comprehend_role_arn
  }
}

# Placeholder Lambda deployment package
data "archive_file" "lambda_placeholder" {
  type        = "zip"
  output_path = "${path.module}/lambda_placeholder.zip"

  source {
    content  = "def handler(event, context): return {'statusCode': 200}"
    filename = "handler.py"
  }
}

# Transcript Processor Lambda
resource "aws_lambda_function" "transcript_processor" {
  function_name = "${var.name_prefix}-transcript-processor"
  role          = var.lambda_execution_role_arn
  handler       = "handlers.transcript_processor.handler"
  runtime       = local.runtime
  timeout       = local.timeout
  memory_size   = local.memory_size

  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256

  environment {
    variables = local.common_env_vars
  }

  tracing_config {
    mode = "Active"
  }

  tags = {
    Name = "${var.name_prefix}-transcript-processor"
  }
}

resource "aws_cloudwatch_log_group" "transcript_processor" {
  name              = "/aws/lambda/${aws_lambda_function.transcript_processor.function_name}"
  retention_in_days = var.log_retention_days
}

# S3 trigger for transcript processor
resource "aws_lambda_permission" "s3_trigger" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.transcript_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.transcripts_bucket}"
}

resource "aws_s3_bucket_notification" "transcripts" {
  bucket = var.transcripts_bucket

  lambda_function {
    lambda_function_arn = aws_lambda_function.transcript_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "input/"
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.s3_trigger]
}

# Comprehend Handler Lambda
resource "aws_lambda_function" "comprehend_handler" {
  function_name = "${var.name_prefix}-comprehend-handler"
  role          = var.lambda_execution_role_arn
  handler       = "handlers.comprehend_handler.start_batch_job_handler"
  runtime       = local.runtime
  timeout       = local.timeout
  memory_size   = local.memory_size

  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256

  environment {
    variables = local.common_env_vars
  }

  tracing_config {
    mode = "Active"
  }

  tags = {
    Name = "${var.name_prefix}-comprehend-handler"
  }
}

resource "aws_cloudwatch_log_group" "comprehend_handler" {
  name              = "/aws/lambda/${aws_lambda_function.comprehend_handler.function_name}"
  retention_in_days = var.log_retention_days
}

# Result Indexer Lambda
resource "aws_lambda_function" "result_indexer" {
  function_name = "${var.name_prefix}-result-indexer"
  role          = var.lambda_execution_role_arn
  handler       = "handlers.result_indexer.handler"
  runtime       = local.runtime
  timeout       = local.timeout
  memory_size   = local.memory_size

  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256

  environment {
    variables = local.common_env_vars
  }

  tracing_config {
    mode = "Active"
  }

  tags = {
    Name = "${var.name_prefix}-result-indexer"
  }
}

resource "aws_cloudwatch_log_group" "result_indexer" {
  name              = "/aws/lambda/${aws_lambda_function.result_indexer.function_name}"
  retention_in_days = var.log_retention_days
}

# S3 trigger for result indexer
resource "aws_lambda_permission" "output_s3_trigger" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.result_indexer.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.output_bucket}"
}

resource "aws_s3_bucket_notification" "output" {
  bucket = var.output_bucket

  lambda_function {
    lambda_function_arn = aws_lambda_function.result_indexer.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "comprehend-output/"
  }

  depends_on = [aws_lambda_permission.output_s3_trigger]
}

# API Handler Lambda
resource "aws_lambda_function" "api_handler" {
  function_name = "${var.name_prefix}-api-handler"
  role          = var.lambda_execution_role_arn
  handler       = "handlers.api_handler.handler"
  runtime       = local.runtime
  timeout       = 30
  memory_size   = 256

  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256

  environment {
    variables = local.common_env_vars
  }

  tracing_config {
    mode = "Active"
  }

  tags = {
    Name = "${var.name_prefix}-api-handler"
  }
}

resource "aws_cloudwatch_log_group" "api_handler" {
  name              = "/aws/lambda/${aws_lambda_function.api_handler.function_name}"
  retention_in_days = var.log_retention_days
}

# Outputs
output "transcript_processor_arn" {
  value = aws_lambda_function.transcript_processor.arn
}

output "transcript_processor_function_name" {
  value = aws_lambda_function.transcript_processor.function_name
}

output "comprehend_handler_arn" {
  value = aws_lambda_function.comprehend_handler.arn
}

output "comprehend_handler_function_name" {
  value = aws_lambda_function.comprehend_handler.function_name
}

output "result_indexer_arn" {
  value = aws_lambda_function.result_indexer.arn
}

output "result_indexer_function_name" {
  value = aws_lambda_function.result_indexer.function_name
}

output "api_handler_arn" {
  value = aws_lambda_function.api_handler.arn
}

output "api_handler_function_name" {
  value = aws_lambda_function.api_handler.function_name
}

output "api_handler_invoke_arn" {
  value = aws_lambda_function.api_handler.invoke_arn
}
