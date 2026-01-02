################################################################################
# Pinpoint Module - Outputs
################################################################################

output "app_id" {
  description = "Pinpoint application ID"
  value       = aws_pinpoint_app.sms_app.application_id
}

output "app_arn" {
  description = "Pinpoint application ARN"
  value       = aws_pinpoint_app.sms_app.arn
}

output "welcome_template_name" {
  description = "Welcome SMS template name"
  value       = aws_pinpoint_sms_template.welcome.template_name
}

output "confirmation_template_name" {
  description = "Confirmation SMS template name"
  value       = aws_pinpoint_sms_template.confirmation.template_name
}

output "promotional_template_name" {
  description = "Promotional SMS template name"
  value       = aws_pinpoint_sms_template.promotional.template_name
}
