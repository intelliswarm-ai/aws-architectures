# SNS Topics

resource "aws_sns_topic" "success" {
  name = "${var.project_prefix}-success"
  tags = var.tags
}

resource "aws_sns_topic" "failure" {
  name = "${var.project_prefix}-failure"
  tags = var.tags
}

resource "aws_sns_topic" "alert" {
  name = "${var.project_prefix}-alert"
  tags = var.tags
}

# Email subscriptions (optional)
resource "aws_sns_topic_subscription" "success_email" {
  count     = var.enable_email_notifications && var.notification_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.success.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

resource "aws_sns_topic_subscription" "failure_email" {
  count     = var.enable_email_notifications && var.notification_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.failure.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

resource "aws_sns_topic_subscription" "alert_email" {
  count     = var.enable_email_notifications && var.notification_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alert.arn
  protocol  = "email"
  endpoint  = var.notification_email
}
