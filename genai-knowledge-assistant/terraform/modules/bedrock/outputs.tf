output "knowledge_base_id" {
  description = "Knowledge Base ID"
  value       = aws_bedrockagent_knowledge_base.main.id
}

output "knowledge_base_arn" {
  description = "Knowledge Base ARN"
  value       = aws_bedrockagent_knowledge_base.main.arn
}

output "data_source_id" {
  description = "Data Source ID"
  value       = aws_bedrockagent_data_source.s3.data_source_id
}

output "agent_id" {
  description = "Agent ID"
  value       = var.create_agent ? aws_bedrockagent_agent.main[0].id : null
}

output "agent_alias_id" {
  description = "Agent Alias ID"
  value       = var.create_agent ? aws_bedrockagent_agent_alias.main[0].agent_alias_id : null
}

output "agent_arn" {
  description = "Agent ARN"
  value       = var.create_agent ? aws_bedrockagent_agent.main[0].agent_arn : null
}
