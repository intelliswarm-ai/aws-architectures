output "success_topic_arn" {
  description = "ARN of the success notification topic"
  value       = aws_sns_topic.success.arn
}

output "success_topic_name" {
  description = "Name of the success notification topic"
  value       = aws_sns_topic.success.name
}

output "failure_topic_arn" {
  description = "ARN of the failure notification topic"
  value       = aws_sns_topic.failure.arn
}

output "failure_topic_name" {
  description = "Name of the failure notification topic"
  value       = aws_sns_topic.failure.name
}
