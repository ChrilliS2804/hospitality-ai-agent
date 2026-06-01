"""Lambda entry point — referenced as call_handler.lambda_function.handler in Terraform."""

from call_handler.api.handler import handler as lambda_handler  # noqa: F401

# AWS Lambda looks for: module.function_name
# Terraform sets handler = "lambda_function.lambda_handler"
