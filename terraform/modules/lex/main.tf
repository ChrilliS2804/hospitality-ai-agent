# Amazon Lex V2 bot — passthrough for speech-to-text
#
# This bot has NO custom intents. All speech is caught by FallbackIntent,
# which invokes our call-handler Lambda with the transcribed text.
# The Lambda calls Bedrock and returns the response to speak.
#
# The bot acts purely as a speech-to-text bridge between Connect and Lambda.

# IAM role for the Lex bot
resource "aws_iam_role" "lex_bot" {
  name = "${var.name_prefix}-lex-bot-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lexv2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "lex_bot" {
  role       = aws_iam_role.lex_bot.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonLexFullAccess"
}

# The Lex V2 bot
resource "aws_lexv2models_bot" "main" {
  name     = "${var.name_prefix}-speech-bot"
  role_arn = aws_iam_role.lex_bot.arn

  data_privacy {
    child_directed = false
  }

  idle_session_ttl_in_seconds = 300

  tags = var.tags
}

# German locale for the bot
resource "aws_lexv2models_bot_locale" "de" {
  bot_id                           = aws_lexv2models_bot.main.id
  bot_version                      = "DRAFT"
  locale_id                        = "de_DE"
  n_lu_intent_confidence_threshold = 0.4

  voice_settings {
    voice_id = "Vicki"
    engine   = "neural"
  }
}

# FallbackIntent — catches all speech input
resource "aws_lexv2models_intent" "fallback" {
  bot_id      = aws_lexv2models_bot.main.id
  bot_version = "DRAFT"
  locale_id   = aws_lexv2models_bot_locale.de.locale_id
  name        = "FallbackIntent"

  parent_intent_signature = "AMAZON.FallbackIntent"

  fulfillment_code_hook {
    enabled = true
  }
}

# Bot version (required for alias)
resource "aws_lexv2models_bot_version" "v1" {
  bot_id = aws_lexv2models_bot.main.id

  locale_specification = {
    "de_DE" = {
      source_bot_version = "DRAFT"
    }
  }

  depends_on = [aws_lexv2models_intent.fallback]
}

# Bot alias — Connect references this
resource "aws_lexv2models_bot_alias" "live" {
  bot_id      = aws_lexv2models_bot.main.id
  bot_version = aws_lexv2models_bot_version.v1.bot_version
  name        = "live"

  bot_alias_locale_settings {
    locale_id = "de_DE"
    bot_alias_locale_setting {
      enabled = true
      code_hook_specification {
        lambda_code_hook {
          lambda_arn                     = var.call_handler_lambda_arn
          code_hook_interface_version    = "1.0"
        }
      }
    }
  }

  tags = var.tags
}

# Allow Lex to invoke the Lambda
resource "aws_lambda_permission" "lex_invoke" {
  statement_id  = "AllowLexInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.call_handler_lambda_arn
  principal     = "lexv2.amazonaws.com"
  source_arn    = aws_lexv2models_bot_alias.live.arn
}
