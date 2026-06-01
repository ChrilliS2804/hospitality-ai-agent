# Lambda layer — shared hospitality library
# The layer zip is built by `make build-layer` and uploaded to S3

resource "aws_lambda_layer_version" "shared" {
  layer_name          = "${var.name_prefix}-shared-layer"
  description         = "Hospitality AI shared library (boto3, pydantic, xray)"
  s3_bucket           = var.lambda_packages_bucket
  s3_key              = "shared-layer.zip"
  compatible_runtimes = ["python3.12"]

  lifecycle {
    create_before_destroy = true
  }
}
