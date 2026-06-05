terraform {
  required_version = ">= 1.7.0"

  backend "s3" {
    # Values supplied via backend.tfvars at init time:
    # terraform init -backend-config=backend.tfvars
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "hospitality-ai"
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "hospitality-ai-agent"
      Application = "AIHospitalityAgent"
    }
  }
}

# ── Variables (re-declared here; values from terraform.tfvars) ────────────────

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "aws_account_id" {
  type = string
}

variable "lambda_log_retention_days" {
  type    = number
  default = 7
}

variable "dynamodb_point_in_time_recovery" {
  type    = bool
  default = false
}

variable "lambda_reserved_concurrency" {
  type    = number
  default = -1
}

variable "create_layer" {
  description = "Set to true after shared-layer.zip has been uploaded to S3"
  type        = bool
  default     = true
}

locals {
  common_tags = {
    Project     = "hospitality-ai"
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = "hospitality-ai-agent"
    Application = "AIHospitalityAgent"
  }
}

# ── Data sources ──────────────────────────────────────────────────────────────

data "aws_availability_zones" "available" {
  state = "available"
}

# ── S3 bucket for Lambda packages and Terraform state ────────────────────────

resource "aws_s3_bucket" "lambda_packages" {
  bucket = "${var.aws_account_id}-hospitality-ai-${var.environment}-lambda-packages"
  tags   = merge(local.common_tags, { Name = "Lambda deployment packages" })
}

resource "aws_s3_bucket_versioning" "lambda_packages" {
  bucket = aws_s3_bucket.lambda_packages.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_packages" {
  bucket = aws_s3_bucket.lambda_packages.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "lambda_packages" {
  bucket                  = aws_s3_bucket.lambda_packages.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── Modules ───────────────────────────────────────────────────────────────────

module "security" {
  source         = "../../modules/security"
  environment    = var.environment
  aws_account_id = var.aws_account_id
  aws_region     = var.aws_region
  name_prefix    = "hospitality-ai-${var.environment}"
  tags           = local.common_tags
}

module "networking" {
  source             = "../../modules/networking"
  name_prefix        = "hospitality-ai-${var.environment}"
  aws_region         = var.aws_region
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2)
  tags               = local.common_tags
}

module "dynamodb" {
  source                 = "../../modules/dynamodb"
  table_name             = "hospitality-ai-${var.environment}-table"
  kms_key_arn            = module.security.kms_key_arn
  point_in_time_recovery = var.dynamodb_point_in_time_recovery
  tags                   = local.common_tags
}

module "lambda" {
  source                            = "../../modules/lambda"
  environment                       = var.environment
  name_prefix                       = "hospitality-ai-${var.environment}"
  aws_region                        = var.aws_region
  aws_account_id                    = var.aws_account_id
  dynamodb_table_arn                = module.dynamodb.table_arn
  dynamodb_table_name               = module.dynamodb.table_name
  kms_key_arn                       = module.security.kms_key_arn
  lambda_packages_bucket            = aws_s3_bucket.lambda_packages.bucket
  log_retention_days                = var.lambda_log_retention_days
  reserved_concurrency_call_handler = var.lambda_reserved_concurrency
  xray_enabled                      = true
  create_layer                      = var.create_layer
  tags                              = local.common_tags
}

module "connect" {
  source                         = "../../modules/connect"
  name_prefix                    = "hospitality-ai-${var.environment}"
  environment                    = var.environment
  call_handler_lambda_arn        = module.lambda.call_handler_arn
  call_handler_lambda_invoke_arn = module.lambda.call_handler_invoke_arn
  tags                           = local.common_tags
}

# Lex V2 bot is created via CLI (see docs/runbooks/lex-bot-setup.md)
# Terraform Lex V2 support is incomplete for bot aliases.

# ── Outputs ───────────────────────────────────────────────────────────────────

output "dynamodb_table_name" {
  value = module.dynamodb.table_name
}

output "call_handler_function_name" {
  value = module.lambda.call_handler_name
}

output "connect_instance_id" {
  value = module.connect.instance_id
}

output "lambda_packages_bucket" {
  value = aws_s3_bucket.lambda_packages.bucket
}
