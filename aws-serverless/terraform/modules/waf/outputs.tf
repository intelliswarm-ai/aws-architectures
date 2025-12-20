# =============================================================================
# WAF Module Outputs
# =============================================================================

output "web_acl_id" {
  description = "WAF Web ACL ID"
  value       = aws_wafv2_web_acl.this.id
}

output "web_acl_arn" {
  description = "WAF Web ACL ARN"
  value       = aws_wafv2_web_acl.this.arn
}

output "web_acl_name" {
  description = "WAF Web ACL name"
  value       = aws_wafv2_web_acl.this.name
}

output "web_acl_capacity" {
  description = "WAF Web ACL capacity units consumed"
  value       = aws_wafv2_web_acl.this.capacity
}

output "allowed_ip_set_arn" {
  description = "Allowed IP set ARN"
  value       = length(var.allowed_ip_addresses) > 0 ? aws_wafv2_ip_set.allowed[0].arn : null
}

output "blocked_ip_set_arn" {
  description = "Blocked IP set ARN"
  value       = length(var.blocked_ip_addresses) > 0 ? aws_wafv2_ip_set.blocked[0].arn : null
}

output "log_group_name" {
  description = "WAF log group name"
  value       = var.enable_logging ? aws_cloudwatch_log_group.waf[0].name : null
}

output "log_group_arn" {
  description = "WAF log group ARN"
  value       = var.enable_logging ? aws_cloudwatch_log_group.waf[0].arn : null
}
