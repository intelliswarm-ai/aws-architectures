################################################################################
# IAM Module - Outputs
################################################################################

output "pinpoint_kinesis_role_arn" {
  description = "ARN of the Pinpoint to Kinesis role"
  value       = aws_iam_role.pinpoint_kinesis.arn
}

output "event_processor_role_arn" {
  description = "ARN of the event processor Lambda role"
  value       = aws_iam_role.event_processor.arn
}

output "response_handler_role_arn" {
  description = "ARN of the response handler Lambda role"
  value       = aws_iam_role.response_handler.arn
}

output "analytics_processor_role_arn" {
  description = "ARN of the analytics processor Lambda role"
  value       = aws_iam_role.analytics_processor.arn
}

output "archive_consumer_role_arn" {
  description = "ARN of the archive consumer Lambda role"
  value       = aws_iam_role.archive_consumer.arn
}
