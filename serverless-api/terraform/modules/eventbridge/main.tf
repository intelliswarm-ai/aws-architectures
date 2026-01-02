# EventBridge Rule for scheduled task generation
resource "aws_cloudwatch_event_rule" "scheduled" {
  name                = var.rule_name
  description         = var.description
  schedule_expression = var.schedule_expression
  state               = var.enabled ? "ENABLED" : "DISABLED"

  tags = var.tags
}

# Target: Lambda function
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.scheduled.name
  target_id = "${var.rule_name}-target"
  arn       = var.lambda_arn

  # Optional: Use the Lambda alias if SnapStart is enabled
  # arn = var.use_alias ? var.lambda_alias_arn : var.lambda_arn

  # Retry policy
  retry_policy {
    maximum_event_age_in_seconds = var.maximum_event_age
    maximum_retry_attempts       = var.maximum_retry_attempts
  }

  # Dead letter queue (optional)
  dynamic "dead_letter_config" {
    for_each = var.dlq_arn != "" ? [1] : []
    content {
      arn = var.dlq_arn
    }
  }
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled.arn
}
