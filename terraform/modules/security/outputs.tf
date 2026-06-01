output "kms_key_arn" {
  description = "ARN of the customer-managed KMS key"
  value       = aws_kms_key.main.arn
}

output "kms_key_id" {
  description = "ID of the customer-managed KMS key"
  value       = aws_kms_key.main.key_id
}

output "kms_alias_arn" {
  description = "ARN of the KMS key alias"
  value       = aws_kms_alias.main.arn
}
