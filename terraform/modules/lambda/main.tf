# Lambda functions — one per microservice
# Sprint 1: call-handler only. Other functions added in Sprints 3-5.

# ── CloudWatch Log Groups (created before functions to control retention) ─────

resource "aws_cloudwatch_log_group" "call_handler" {
  name              = "/aws/lambda/${var.name_prefix}-call-handler"
  retention_in_days = var.log_retention_days
  # KMS encryption added in Sprint 6 hardening after key policy propagation
  # kms_key_id = var.kms_key_arn
  tags              = var.tags
}

# ── Call Handler Lambda ───────────────────────────────────────────────────────

resource "aws_lambda_function" "call_handler" {
  function_name = "${var.name_prefix}-call-handler"
  description   = "Orchestrator Lambda - handles Amazon Connect inbound calls"
  role          = aws_iam_role.call_handler.arn

  s3_bucket = var.lambda_packages_bucket
  s3_key    = "call-handler.zip"

  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  timeout       = 29   # Connect timeout is ~30s; stay under it
  memory_size   = 512  # Tuned in Sprint 6 based on metrics

  layers = var.create_layer ? [aws_lambda_layer_version.shared[0].arn] : []

  environment {
    variables = {
      ENVIRONMENT         = var.environment
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
      AWS_REGION_NAME     = var.aws_region
      LOG_LEVEL           = var.environment == "prod" ? "INFO" : "DEBUG"
      XRAY_ENABLED        = tostring(var.xray_enabled)
      SESSION_TTL_SECONDS = "86400"
      BEDROCK_MODEL_ID    = "anthropic.claude-3-5-sonnet-20241022-v2:0"
      BEDROCK_MAX_TOKENS  = "1024"
      BEDROCK_TEMPERATURE = "0.3"
    }
  }

  kms_key_arn = var.kms_key_arn

  tracing_config {
    mode = var.xray_enabled ? "Active" : "PassThrough"
  }

  # -1 means unreserved (use account default). Only set when explicitly configured.
  reserved_concurrent_executions = var.reserved_concurrency_call_handler >= 0 ? var.reserved_concurrency_call_handler : null

  depends_on = [
    aws_cloudwatch_log_group.call_handler,
    aws_iam_role_policy.call_handler,
  ]

  tags = var.tags

  lifecycle {
    ignore_changes = [
      # S3 object version managed by CI/CD deploy step
      s3_object_version,
    ]
  }
}

# Allow Amazon Connect to invoke the call handler
resource "aws_lambda_permission" "connect_invoke_call_handler" {
  statement_id  = "AllowConnectInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.call_handler.function_name
  principal     = "connect.amazonaws.com"
  source_arn    = "arn:aws:connect:${var.aws_region}:${var.aws_account_id}:instance/*"
}
