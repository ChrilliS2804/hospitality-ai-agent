# Common local values shared across all modules and environments

locals {
  # Injected by each environment's terraform.tfvars
  project     = "hospitality-ai"
  name_prefix = "${local.project}-${var.environment}"

  # Standard tags applied to every resource
  common_tags = {
    Project     = local.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = "hospitality-ai-agent"
    Application = "AIHospitalityAgent"
  }

  # DynamoDB single global table name
  dynamodb_table_name = "${local.name_prefix}-table"

  # Lambda function names
  lambda_names = {
    call_handler         = "${local.name_prefix}-call-handler"
    reservation_service  = "${local.name_prefix}-reservation-service"
    faq_service          = "${local.name_prefix}-faq-service"
    notification_service = "${local.name_prefix}-notification-service"
    handoff_service      = "${local.name_prefix}-handoff-service"
  }

  # CloudWatch log group names
  log_group_names = {
    for k, v in local.lambda_names : k => "/aws/lambda/${v}"
  }

  # EventBridge custom bus name
  event_bus_name = "${local.name_prefix}-events"
}
