################################################################################
# EventBridge Module for GPS Producer Scheduling
################################################################################

resource "aws_cloudwatch_event_rule" "producer_schedule" {
  name                = "${var.project_name}-producer-schedule"
  description         = "Triggers GPS producer Lambda function on schedule"
  schedule_expression = var.schedule_expression

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "producer" {
  rule      = aws_cloudwatch_event_rule.producer_schedule.name
  target_id = "TriggerGPSProducer"
  arn       = var.producer_lambda_arn

  input = jsonencode({
    source = "scheduled"
  })
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.producer_lambda_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.producer_schedule.arn
}
