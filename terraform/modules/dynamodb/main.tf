# Single global DynamoDB table for all entities
# Key design: PK/SK composite with entity-type prefixes
# GSI1: availability queries (reservations by tenant+date)
# GSI2: lookup by caller phone + date

resource "aws_dynamodb_table" "main" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST" # On-demand — scales to zero
  hash_key     = "PK"
  range_key    = "SK"

  # Primary key
  attribute {
    name = "PK"
    type = "S"
  }
  attribute {
    name = "SK"
    type = "S"
  }

  # GSI1 keys — reservation availability by tenant+date, session list by tenant
  attribute {
    name = "GSI1PK"
    type = "S"
  }
  attribute {
    name = "GSI1SK"
    type = "S"
  }

  # GSI2 keys — reservation lookup by caller phone+date
  attribute {
    name = "GSI2PK"
    type = "S"
  }
  attribute {
    name = "GSI2SK"
    type = "S"
  }

  # GSI1: availability check and session listing
  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"
  }

  # GSI2: find reservation by caller phone
  global_secondary_index {
    name            = "GSI2"
    hash_key        = "GSI2PK"
    range_key       = "GSI2SK"
    projection_type = "ALL"
  }

  # TTL for automatic session cleanup (24h)
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Encryption at rest with customer-managed KMS key
  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  # Point-in-time recovery (enabled in prod)
  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }

  tags = var.tags
}
