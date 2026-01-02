output "data_sensitivity_tag_key" {
  description = "Key of the data sensitivity LF-Tag"
  value       = aws_lakeformation_lf_tag.sensitivity.key
}

output "data_domain_tag_key" {
  description = "Key of the data domain LF-Tag"
  value       = aws_lakeformation_lf_tag.domain.key
}
