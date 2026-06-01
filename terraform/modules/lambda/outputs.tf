output "call_handler_arn" {
  description = "ARN of the call handler Lambda function"
  value       = aws_lambda_function.call_handler.arn
}

output "call_handler_name" {
  description = "Name of the call handler Lambda function"
  value       = aws_lambda_function.call_handler.function_name
}

output "call_handler_invoke_arn" {
  description = "Invoke ARN of the call handler (used by Amazon Connect)"
  value       = aws_lambda_function.call_handler.invoke_arn
}

output "shared_layer_arn" {
  description = "ARN of the shared Lambda layer"
  value       = aws_lambda_layer_version.shared.arn
}
