output "app_security_group_id" {
  description = "Application security group ID"
  value       = aws_security_group.app.id
}

output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}
