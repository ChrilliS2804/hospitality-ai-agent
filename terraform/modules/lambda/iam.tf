# IAM roles and policies — one role per Lambda function (least privilege)

# ── Shared assume-role policy for all Lambda functions ────────────────────────

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# ── Call Handler ──────────────────────────────────────────────────────────────

resource "aws_iam_role" "call_handler" {
  name               = "${var.name_prefix}-call-handler-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy" "call_handler" {
  name   = "${var.name_prefix}-call-handler-policy"
  role   = aws_iam_role.call_handler.id
  policy = data.aws_iam_policy_document.call_handler_policy.json
}

data "aws_iam_policy_document" "call_handler_policy" {
  # CloudWatch Logs
  statement {
    sid    = "Logs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/aws/lambda/${var.name_prefix}-call-handler:*"]
  }

  # DynamoDB — sessions only (PK prefix SESSION#)
  statement {
    sid    = "DynamoDBSessions"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
    ]
    resources = [
      var.dynamodb_table_arn,
      "${var.dynamodb_table_arn}/index/*",
    ]
  }

  # Bedrock — invoke model for NLU (cross-region inference profile)
  statement {
    sid    = "BedrockInvoke"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
      "bedrock:GetInferenceProfile",
      "bedrock:ListInferenceProfiles",
    ]
    resources = [
      "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.*",
      "arn:aws:bedrock:eu:${var.aws_account_id}:inference-profile/eu.anthropic.*",
      "arn:aws:bedrock:*::foundation-model/anthropic.*",
    ]
  }

  # Lambda — invoke downstream services
  statement {
    sid    = "InvokeServices"
    effect = "Allow"
    actions = ["lambda:InvokeFunction"]
    resources = [
      "arn:aws:lambda:${var.aws_region}:${var.aws_account_id}:function:${var.name_prefix}-reservation-service",
      "arn:aws:lambda:${var.aws_region}:${var.aws_account_id}:function:${var.name_prefix}-faq-service",
      "arn:aws:lambda:${var.aws_region}:${var.aws_account_id}:function:${var.name_prefix}-handoff-service",
    ]
  }

  # X-Ray tracing
  statement {
    sid    = "XRay"
    effect = "Allow"
    actions = [
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
    ]
    resources = ["*"]
  }

  # KMS — decrypt environment variables
  statement {
    sid    = "KMSDecrypt"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
    ]
    resources = [var.kms_key_arn]
  }
}

# Attach AWS managed policy for basic Lambda execution
resource "aws_iam_role_policy_attachment" "call_handler_basic" {
  role       = aws_iam_role.call_handler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
