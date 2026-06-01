variable "environment" {
  description = "Deployment environment (dev, test, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be one of: dev, test, prod"
  }
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-central-1"
}

variable "aws_account_id" {
  description = "AWS account ID (used for IAM ARN construction)"
  type        = string
}

variable "lambda_log_retention_days" {
  description = "CloudWatch log retention in days for Lambda functions"
  type        = number
  default     = 30
}

variable "dynamodb_point_in_time_recovery" {
  description = "Enable DynamoDB point-in-time recovery"
  type        = bool
  default     = false # true in prod
}

variable "lambda_reserved_concurrency" {
  description = "Reserved concurrency for call-handler Lambda (-1 = unreserved)"
  type        = number
  default     = -1
}

variable "tags" {
  description = "Additional tags to merge with common_tags"
  type        = map(string)
  default     = {}
}
