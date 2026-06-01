variable "name_prefix" {
  type = string
}

variable "environment" {
  type = string
}

variable "call_handler_lambda_arn" {
  description = "ARN of the call handler Lambda function"
  type        = string
}

variable "call_handler_lambda_invoke_arn" {
  description = "Invoke ARN of the call handler Lambda"
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
