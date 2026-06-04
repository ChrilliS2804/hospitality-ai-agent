# Contact Flow definition (JSON) - Amazon Connect Contact Flow format
# Sprint 1: Set tenant → Invoke Lambda → Speak response → Get input → Loop
# Uses the current Amazon Connect Contact Flow JSON schema (2019-10-30)

locals {
  contact_flow_content = jsonencode({
    Version     = "2019-10-30"
    StartAction = "set-tenant-attribute"
    Actions = [
      {
        Identifier = "set-tenant-attribute"
        Type       = "UpdateContactAttributes"
        Parameters = {
          Attributes = {
            tenant_id = {
              Value = "default"
            }
          }
        }
        Transitions = {
          NextAction = "invoke-lambda"
          Errors     = []
          Conditions = []
        }
      },
      {
        Identifier = "invoke-lambda"
        Type       = "InvokeLambdaFunction"
        Parameters = {
          LambdaFunctionARN = {
            Value = var.call_handler_lambda_invoke_arn
          }
          InvocationTimeLimitSeconds = {
            Value = "8"
          }
          LambdaInvocationAttributes = {
            userInput = {
              Value         = "$.Attributes.userInput"
              ValueType     = "Attribute"
              AttributeType = "UserDefined"
            }
          }
          ResponseValidation = {
            ResponseType = "STRING_MAP"
          }
        }
        Transitions = {
          NextAction = "speak-response"
          Errors = [
            {
              NextAction = "error-prompt"
              ErrorType  = "NoMatchingError"
            }
          ]
          Conditions = []
        }
      },
      {
        Identifier = "speak-response"
        Type       = "MessageParticipant"
        Parameters = {
          Text = {
            Value         = "$.External.response"
            ValueType     = "Attribute"
            AttributeType = "External"
          }
          SSML = {
            Value = "false"
          }
          LanguageCode = {
            Value = "en-US"
          }
        }
        Transitions = {
          NextAction = "get-customer-input"
          Errors = [
            {
              NextAction = "error-prompt"
              ErrorType  = "NoMatchingError"
            }
          ]
          Conditions = []
        }
      },
      {
        Identifier = "get-customer-input"
        Type       = "GetParticipantInput"
        Parameters = {
          Text = {
            Value = "How else can I help you?"
          }
          SSML = {
            Value = "false"
          }
          LanguageCode = {
            Value = "en-US"
          }
          Timeout = {
            Value = "8"
          }
          MaxDigits = {
            Value = "0"
          }
          InputTimeLimitSeconds = {
            Value = "8"
          }
        }
        Transitions = {
          NextAction = "store-input"
          Errors = [
            {
              NextAction = "invoke-lambda"
              ErrorType  = "InputTimeLimitExceeded"
            },
            {
              NextAction = "error-prompt"
              ErrorType  = "NoMatchingError"
            }
          ]
          Conditions = []
        }
      },
      {
        Identifier = "store-input"
        Type       = "UpdateContactAttributes"
        Parameters = {
          Attributes = {
            userInput = {
              Value         = "$.CustomerInput.SpeechResult"
              ValueType     = "Attribute"
              AttributeType = "System"
            }
          }
        }
        Transitions = {
          NextAction = "invoke-lambda"
          Errors     = []
          Conditions = []
        }
      },
      {
        Identifier = "error-prompt"
        Type       = "MessageParticipant"
        Parameters = {
          Text = {
            Value = "I am sorry, something went wrong. Please call back and we will be happy to help."
          }
          SSML = {
            Value = "false"
          }
          LanguageCode = {
            Value = "en-US"
          }
        }
        Transitions = {
          NextAction = "disconnect"
          Errors = [
            {
              NextAction = "disconnect"
              ErrorType  = "NoMatchingError"
            }
          ]
          Conditions = []
        }
      },
      {
        Identifier  = "disconnect"
        Type        = "DisconnectParticipant"
        Parameters  = {}
        Transitions = {}
      }
    ]
  })
}
