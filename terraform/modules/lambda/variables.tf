variable "environment" {
  type = string
}

variable "name_prefix" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "aws_account_id" {
  type = string
}

variable "dynamodb_table_arn" {
  description = "ARN of the single global DynamoDB table"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the single global DynamoDB table"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for Lambda environment variable encryption"
  type        = string
}

variable "lambda_packages_bucket" {
  description = "S3 bucket containing Lambda deployment packages"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "reserved_concurrency_call_handler" {
  description = "Reserved concurrency for call-handler (-1 = unreserved)"
  type        = number
  default     = -1
}

variable "xray_enabled" {
  description = "Enable X-Ray active tracing"
  type        = bool
  default     = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
