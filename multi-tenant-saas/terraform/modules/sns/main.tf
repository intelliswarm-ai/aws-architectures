# =============================================================================
# SNS Module
# =============================================================================

resource "aws_sns_topic" "notification" {
  name              = "${var.name_prefix}-notifications"
  kms_master_key_id = var.enable_encryption ? var.kms_key_id : null
  tags              = var.tags
}

resource "aws_sns_topic" "alert" {
  name              = "${var.name_prefix}-alerts"
  kms_master_key_id = var.enable_encryption ? var.kms_key_id : null
  tags              = var.tags
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.notification_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alert.arn
  protocol  = "email"
  endpoint  = var.notification_email
}
