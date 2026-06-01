output "dynamodb_table_name" {
  description = "Name of the single global DynamoDB table"
  value       = module.dynamodb.table_name
}

output "dynamodb_table_arn" {
  description = "ARN of the single global DynamoDB table"
  value       = module.dynamodb.table_arn
}

output "call_handler_function_arn" {
  description = "ARN of the call handler Lambda function"
  value       = module.lambda.call_handler_arn
}

output "call_handler_function_name" {
  description = "Name of the call handler Lambda function"
  value       = module.lambda.call_handler_name
}

output "kms_key_arn" {
  description = "ARN of the KMS key used for encryption"
  value       = module.security.kms_key_arn
}
