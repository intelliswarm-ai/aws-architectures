# Dead Letter Queue
resource "aws_sqs_queue" "dlq" {
  name                       = "${var.queue_name}-dlq"
  message_retention_seconds  = var.dlq_message_retention
  visibility_timeout_seconds = var.visibility_timeout

  # Enable server-side encryption
  sqs_managed_sse_enabled = true

  tags = var.tags
}

# Main Task Queue
resource "aws_sqs_queue" "main" {
  name                       = var.queue_name
  delay_seconds              = var.delay_seconds
  max_message_size           = var.max_message_size
  message_retention_seconds  = var.message_retention
  receive_wait_time_seconds  = var.receive_wait_time
  visibility_timeout_seconds = var.visibility_timeout

  # Enable server-side encryption
  sqs_managed_sse_enabled = true

  # Redrive policy to send failed messages to DLQ
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = var.tags
}

# Allow the DLQ to receive messages from the main queue
resource "aws_sqs_queue_redrive_allow_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.main.arn]
  })
}

# Queue policy for allowing Lambda and other services to access
resource "aws_sqs_queue_policy" "main" {
  count     = var.queue_policy != null ? 1 : 0
  queue_url = aws_sqs_queue.main.id
  policy    = var.queue_policy
}
