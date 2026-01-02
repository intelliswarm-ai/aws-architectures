# ---------------------------------------------------------------------------------------------------------------------
# EVENTBRIDGE SCHEDULED RULES FOR ETL
# ---------------------------------------------------------------------------------------------------------------------

# Scheduled rule for hourly ETL execution
resource "aws_cloudwatch_event_rule" "etl_schedule" {
  name                = "${var.project_name}-${var.environment}-etl-schedule"
  description         = "Trigger ETL job on schedule"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "etl_lambda" {
  rule      = aws_cloudwatch_event_rule.etl_schedule.name
  target_id = "TriggerETLLambda"
  arn       = var.etl_lambda_arn

  input = jsonencode({
    source = "scheduled"
    action = "start"
  })
}

resource "aws_lambda_permission" "eventbridge_etl" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.etl_lambda_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.etl_schedule.arn
}
