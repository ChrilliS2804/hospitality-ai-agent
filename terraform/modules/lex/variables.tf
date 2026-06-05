variable "name_prefix" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "aws_account_id" {
  type = string
}

variable "call_handler_lambda_arn" {
  description = "ARN of the call handler Lambda function"
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
