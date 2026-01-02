output "success_topic_arn" {
  value = aws_sns_topic.success.arn
}

output "failure_topic_arn" {
  value = aws_sns_topic.failure.arn
}

output "alert_topic_arn" {
  value = aws_sns_topic.alert.arn
}
