output "alerts_topic_arn" {
  description = "Alerts SNS topic ARN"
  value       = aws_sns_topic.alerts.arn
}

output "alerts_topic_name" {
  description = "Alerts SNS topic name"
  value       = aws_sns_topic.alerts.name
}

output "events_topic_arn" {
  description = "Events SNS topic ARN"
  value       = aws_sns_topic.events.arn
}

output "events_topic_name" {
  description = "Events SNS topic name"
  value       = aws_sns_topic.events.name
}
