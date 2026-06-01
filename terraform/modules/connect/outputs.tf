output "instance_id" {
  description = "Amazon Connect instance ID"
  value       = aws_connect_instance.main.id
}

output "instance_arn" {
  description = "Amazon Connect instance ARN"
  value       = aws_connect_instance.main.arn
}

output "contact_flow_id" {
  description = "Inbound contact flow ID"
  value       = aws_connect_contact_flow.inbound.contact_flow_id
}

output "contact_flow_arn" {
  description = "Inbound contact flow ARN"
  value       = aws_connect_contact_flow.inbound.arn
}
