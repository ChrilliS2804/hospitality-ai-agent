# Bootstrap — creates the S3 bucket and DynamoDB table for Terraform remote state.
# Run ONCE per AWS account before any environment init:
#   cd terraform/bootstrap
#   terraform init
#   terraform apply -var="aws_account_id=YOUR_ACCOUNT_ID" -var="aws_region=eu-central-1"

terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.50" }
  }
  # Bootstrap uses local state — it manages the remote state bucket itself
}

variable "aws_account_id" { type = string }
variable "aws_region" { type = string; default = "eu-central-1" }

provider "aws" { region = var.aws_region }

resource "aws_s3_bucket" "tf_state" {
  bucket = "${var.aws_account_id}-hospitality-ai-tf-state"
  tags   = { Name = "Terraform state", ManagedBy = "terraform-bootstrap", Application = "AIHospitalityAgent" }
}

resource "aws_s3_bucket_versioning" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_public_access_block" "tf_state" {
  bucket                  = aws_s3_bucket.tf_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "tf_locks" {
  name         = "hospitality-ai-tf-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  attribute {
    name = "LockID"
    type = "S"
  }
  tags = { Name = "Terraform state locks", ManagedBy = "terraform-bootstrap", Application = "AIHospitalityAgent" }
}

output "state_bucket" { value = aws_s3_bucket.tf_state.bucket }
output "lock_table" { value = aws_dynamodb_table.tf_locks.name }
