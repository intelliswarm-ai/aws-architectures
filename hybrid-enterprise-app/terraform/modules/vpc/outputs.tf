output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "vpn_gateway_id" {
  description = "VPN Gateway ID"
  value       = var.enable_vpn_gateway ? aws_vpn_gateway.main[0].id : null
}

output "vpn_connection_id" {
  description = "VPN Connection ID"
  value       = var.enable_vpn_gateway && var.customer_gateway_ip != "" ? aws_vpn_connection.main[0].id : null
}
