# SQS Queues

resource "aws_sqs_queue" "dlq" {
  name                       = "${var.project_prefix}-processing-dlq"
  message_retention_seconds  = var.message_retention
  visibility_timeout_seconds = var.visibility_timeout
  sqs_managed_sse_enabled    = true
  tags                       = var.tags
}

resource "aws_sqs_queue" "processing" {
  name                       = "${var.project_prefix}-processing"
  delay_seconds              = 0
  max_message_size           = 262144
  message_retention_seconds  = var.message_retention
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = var.visibility_timeout
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = var.tags
}

resource "aws_sqs_queue_redrive_allow_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.processing.arn]
  })
}
