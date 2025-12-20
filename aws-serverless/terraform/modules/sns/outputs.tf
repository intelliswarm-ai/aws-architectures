output "notification_topic_arn" {
  value = aws_sns_topic.notification.arn
}

output "alert_topic_arn" {
  value = aws_sns_topic.alert.arn
}
