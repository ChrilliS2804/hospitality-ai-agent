# Amazon Connect instance and Lambda integration
# NOTE: The Contact Flow is created manually in the AWS Console for Sprint 1.
# The Connect instance and Lambda association are managed by Terraform.
# See docs/runbooks/connect-contact-flow-setup.md for manual setup steps.

resource "aws_connect_instance" "main" {
  identity_management_type = "CONNECT_MANAGED"
  inbound_calls_enabled    = true
  outbound_calls_enabled   = false
  instance_alias           = "${var.name_prefix}-instance"

  tags = var.tags
}

# Associate the call handler Lambda with the Connect instance
resource "aws_connect_lambda_function_association" "call_handler" {
  instance_id  = aws_connect_instance.main.id
  function_arn = var.call_handler_lambda_arn
}
