# SNS Module - Notifications

resource "aws_sns_topic" "alerts" {
  name = "${var.project_prefix}-alerts"

  tags = var.tags
}

resource "aws_sns_topic" "events" {
  name = "${var.project_prefix}-deployment-events"

  tags = var.tags
}

resource "aws_sns_topic_subscription" "alert_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
