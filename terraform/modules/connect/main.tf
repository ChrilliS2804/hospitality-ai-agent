# Amazon Connect instance and Lambda integration
# Note: Phone number claiming is done manually post-deploy (requires AWS Support
# in some regions). The instance and contact flow are fully automated.

resource "aws_connect_instance" "main" {
  identity_management_type = "CONNECT_MANAGED"
  inbound_calls_enabled    = true
  outbound_calls_enabled   = false  # Not needed for MVP
  instance_alias           = "${var.name_prefix}-instance"

  tags = var.tags
}

# Associate the call handler Lambda with the Connect instance
resource "aws_connect_lambda_function_association" "call_handler" {
  instance_id  = aws_connect_instance.main.id
  function_arn = var.call_handler_lambda_arn
}

# Contact Flow — Sprint 1: greeting flow that invokes Lambda on every turn
resource "aws_connect_contact_flow" "inbound" {
  instance_id = aws_connect_instance.main.id
  name        = "${var.name_prefix}-inbound-flow"
  description = "Main inbound contact flow - routes calls to AI agent Lambda"
  type        = "CONTACT_FLOW"
  content     = local.contact_flow_content
  tags        = var.tags
}
