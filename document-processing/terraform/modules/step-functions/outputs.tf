output "document_workflow_arn" {
  value = aws_sfn_state_machine.document_workflow.arn
}

output "document_workflow_name" {
  value = aws_sfn_state_machine.document_workflow.name
}
