output "bot_id" {
  description = "Lex V2 bot ID"
  value       = aws_lexv2models_bot.main.id
}

output "bot_alias_id" {
  description = "Lex V2 bot alias ID (used in Connect contact flow)"
  value       = aws_lexv2models_bot_alias.live.bot_alias_id
}

output "bot_name" {
  description = "Lex V2 bot name"
  value       = aws_lexv2models_bot.main.name
}
