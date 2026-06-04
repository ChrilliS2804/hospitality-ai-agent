output "instance_id" {
  description = "Amazon Connect instance ID"
  value       = aws_connect_instance.main.id
}

output "instance_arn" {
  description = "Amazon Connect instance ARN"
  value       = aws_connect_instance.main.arn
}

output "contact_flow_id" {
  description = "Inbound contact flow ID (set manually after console creation)"
  value       = "MANUAL_SETUP_REQUIRED"
}

output "contact_flow_arn" {
  description = "Inbound contact flow ARN (set manually after console creation)"
  value       = "MANUAL_SETUP_REQUIRED"
}
