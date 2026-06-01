# Contact Flow definition (JSON)
# Sprint 1 flow: Set tenant attribute → Invoke Lambda → Speak response → Loop
# The flow loops back to Lambda on each caller utterance, enabling multi-turn
# conversation. Lambda controls termination via the 'action' field in its response.

locals {
  contact_flow_content = jsonencode({
    Version     = "2019-10-30"
    StartAction = "set-tenant-attribute"
    Actions = [
      # Step 1: Set tenant_id as a contact attribute
      # In production this would be set based on the dialled number (DID routing)
      {
        Identifier = "set-tenant-attribute"
        Type       = "UpdateContactAttributes"
        Parameters = {
          Attributes = {
            tenant_id = "default"
          }
        }
        Transitions = {
          Success = "invoke-lambda"
          Error   = "error-prompt"
        }
      },

      # Step 2: Invoke the call handler Lambda
      {
        Identifier = "invoke-lambda"
        Type       = "InvokeLambdaFunction"
        Parameters = {
          LambdaFunctionARN = var.call_handler_lambda_invoke_arn
          InvocationTimeLimitSeconds = "8"
          LambdaInvocationAttributes = {
            userInput = "$.Attributes.userInput"
          }
        }
        Transitions = {
          Success = "speak-response"
          Error   = "error-prompt"
        }
      },

      # Step 3: Speak the Lambda response to the caller
      {
        Identifier = "speak-response"
        Type       = "MessageParticipant"
        Parameters = {
          Text = "$.External.response"
          TextToSpeechType = "text"
          LanguageCode     = "en-US"
          VoiceId          = "Joanna"
        }
        Transitions = {
          Success = "get-customer-input"
          Error   = "error-prompt"
        }
      },

      # Step 4: Listen for caller input (speech)
      {
        Identifier = "get-customer-input"
        Type       = "GetParticipantInput"
        Parameters = {
          Text             = " "
          InputTimeLimitSeconds = "10"
          TextToSpeechType = "text"
          LanguageCode     = "en-US"
          VoiceId          = "Joanna"
          SpeechParameters = {
            EndpointSilenceDurationMs = "2000"
          }
        }
        Transitions = {
          Success  = "store-input"
          NoMatch  = "invoke-lambda"
          Error    = "error-prompt"
          Timeout  = "invoke-lambda"
        }
      },

      # Step 5: Store caller input as contact attribute, loop back to Lambda
      {
        Identifier = "store-input"
        Type       = "UpdateContactAttributes"
        Parameters = {
          Attributes = {
            userInput = "$.CustomerInput.SpeechResult"
          }
        }
        Transitions = {
          Success = "invoke-lambda"
          Error   = "error-prompt"
        }
      },

      # Error handler — play apology and disconnect
      {
        Identifier = "error-prompt"
        Type       = "MessageParticipant"
        Parameters = {
          Text             = "I'm sorry, something went wrong. Please call back and we'll be happy to help."
          TextToSpeechType = "text"
          LanguageCode     = "en-US"
          VoiceId          = "Joanna"
        }
        Transitions = {
          Success = "disconnect"
          Error   = "disconnect"
        }
      },

      # Disconnect
      {
        Identifier = "disconnect"
        Type       = "DisconnectParticipant"
        Parameters = {}
        Transitions = {}
      }
    ]
  })
}
