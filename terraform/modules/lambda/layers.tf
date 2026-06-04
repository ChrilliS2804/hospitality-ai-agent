# Lambda layer — shared hospitality library
# The layer zip is built and uploaded to S3 BEFORE running terraform apply.
# This resource is gated by the create_layer variable so the first apply
# (infrastructure only) succeeds before the zip exists.

variable "create_layer" {
  description = "Set to true after shared-layer.zip has been uploaded to S3"
  type        = bool
  default     = false
}

resource "aws_lambda_layer_version" "shared" {
  count = var.create_layer ? 1 : 0

  layer_name          = "${var.name_prefix}-shared-layer"
  description         = "Hospitality AI shared library (boto3, pydantic, xray)"
  s3_bucket           = var.lambda_packages_bucket
  s3_key              = "shared-layer.zip"
  compatible_runtimes = ["python3.12"]

  lifecycle {
    create_before_destroy = true
  }
}
