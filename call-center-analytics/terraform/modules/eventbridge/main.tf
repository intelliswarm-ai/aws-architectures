variable "environment" {
  type = string
}

variable "name_prefix" {
  type = string
}

variable "comprehend_handler_arn" {
  type = string
}

variable "comprehend_handler_function_name" {
  type = string
}

# Scheduled rule for batch processing (e.g., daily)
resource "aws_cloudwatch_event_rule" "batch_processing" {
  name                = "${var.name_prefix}-batch-processing"
  description         = "Trigger batch sentiment analysis"
  schedule_expression = "cron(0 2 * * ? *)" # Daily at 2 AM UTC

  tags = {
    Name = "${var.name_prefix}-batch-processing"
  }
}

resource "aws_cloudwatch_event_target" "batch_processing" {
  rule      = aws_cloudwatch_event_rule.batch_processing.name
  target_id = "comprehend-batch"
  arn       = var.comprehend_handler_arn

  input = jsonencode({
    action       = "start_sentiment"
    input_prefix = "input/batch/"
    language     = "en"
  })
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.comprehend_handler_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.batch_processing.arn
}

# Comprehend job completion event
resource "aws_cloudwatch_event_rule" "comprehend_complete" {
  name        = "${var.name_prefix}-comprehend-complete"
  description = "Trigger when Comprehend job completes"

  event_pattern = jsonencode({
    source      = ["aws.comprehend"]
    detail-type = ["Comprehend Analysis Job State Change"]
    detail = {
      JobStatus = ["COMPLETED", "FAILED"]
    }
  })

  tags = {
    Name = "${var.name_prefix}-comprehend-complete"
  }
}

output "batch_processing_rule_arn" {
  value = aws_cloudwatch_event_rule.batch_processing.arn
}
