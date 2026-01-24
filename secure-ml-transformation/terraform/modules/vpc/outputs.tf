output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "vpc_endpoint_security_group_id" {
  description = "VPC endpoint security group ID"
  value       = aws_security_group.vpc_endpoints.id
}

output "glue_security_group_id" {
  description = "Glue security group ID"
  value       = aws_security_group.glue.id
}

output "s3_endpoint_id" {
  description = "S3 VPC endpoint ID"
  value       = aws_vpc_endpoint.s3.id
}
