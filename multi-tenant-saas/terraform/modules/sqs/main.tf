# =============================================================================
# SQS Module
# =============================================================================

resource "aws_sqs_queue" "dlq" {
  name                      = "${var.name_prefix}-dlq"
  message_retention_seconds = var.message_retention
  kms_master_key_id         = var.enable_encryption ? var.kms_key_id : null

  tags = var.tags
}

resource "aws_sqs_queue" "main" {
  name                       = "${var.name_prefix}-queue"
  visibility_timeout_seconds = var.visibility_timeout
  message_retention_seconds  = var.message_retention
  kms_master_key_id          = var.enable_encryption ? var.kms_key_id : null

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = var.tags
}
