# Customer-managed KMS key for DynamoDB, S3, and CloudWatch Logs encryption

resource "aws_kms_key" "main" {
  description             = "${var.name_prefix} encryption key"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = data.aws_iam_policy_document.kms_key_policy.json

  tags = merge(var.tags, { Name = "${var.name_prefix}-key", Application = "AIHospitalityAgent" })
}

resource "aws_kms_alias" "main" {
  name          = "alias/${var.name_prefix}-key"
  target_key_id = aws_kms_key.main.key_id
}

data "aws_iam_policy_document" "kms_key_policy" {
  # Allow root account full control
  statement {
    sid    = "EnableRootAccess"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.aws_account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  # Allow Lambda and DynamoDB service principals to use the key
  statement {
    sid    = "AllowServiceUse"
    effect = "Allow"
    principals {
      type = "Service"
      identifiers = [
        "lambda.amazonaws.com",
        "dynamodb.amazonaws.com",
        "logs.${var.aws_region}.amazonaws.com",
      ]
    }
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]
    resources = ["*"]
  }
}
