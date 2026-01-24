output "key_id" {
  description = "KMS key ID"
  value       = aws_kms_key.encryption.key_id
}

output "key_arn" {
  description = "KMS key ARN"
  value       = aws_kms_key.encryption.arn
}

output "key_alias" {
  description = "KMS key alias"
  value       = aws_kms_alias.encryption.name
}
