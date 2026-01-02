output "producer_role_arn" {
  description = "ARN of the producer role"
  value       = aws_iam_role.producer.arn
}

output "producer_role_name" {
  description = "Name of the producer role"
  value       = aws_iam_role.producer.name
}

output "dashboard_consumer_role_arn" {
  description = "ARN of the dashboard consumer role"
  value       = aws_iam_role.dashboard_consumer.arn
}

output "dashboard_consumer_role_name" {
  description = "Name of the dashboard consumer role"
  value       = aws_iam_role.dashboard_consumer.name
}

output "geofence_consumer_role_arn" {
  description = "ARN of the geofence consumer role"
  value       = aws_iam_role.geofence_consumer.arn
}

output "geofence_consumer_role_name" {
  description = "Name of the geofence consumer role"
  value       = aws_iam_role.geofence_consumer.name
}

output "archive_consumer_role_arn" {
  description = "ARN of the archive consumer role"
  value       = aws_iam_role.archive_consumer.arn
}

output "archive_consumer_role_name" {
  description = "Name of the archive consumer role"
  value       = aws_iam_role.archive_consumer.name
}
