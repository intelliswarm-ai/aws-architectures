output "positions_table_name" {
  description = "Name of the positions table"
  value       = aws_dynamodb_table.positions.name
}

output "positions_table_arn" {
  description = "ARN of the positions table"
  value       = aws_dynamodb_table.positions.arn
}

output "geofences_table_name" {
  description = "Name of the geofences table"
  value       = aws_dynamodb_table.geofences.name
}

output "geofences_table_arn" {
  description = "ARN of the geofences table"
  value       = aws_dynamodb_table.geofences.arn
}
