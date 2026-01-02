output "lambda_sg_id" {
  description = "Lambda security group ID"
  value       = aws_security_group.lambda.id
}

output "vpc_endpoints_sg_id" {
  description = "VPC endpoints security group ID"
  value       = aws_security_group.vpc_endpoints.id
}

output "database_sg_id" {
  description = "Database security group ID"
  value       = var.create_database_sg ? aws_security_group.database[0].id : null
}

output "cache_sg_id" {
  description = "Cache security group ID"
  value       = var.create_cache_sg ? aws_security_group.cache[0].id : null
}
