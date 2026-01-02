variable "name_prefix" {
  type = string
}

variable "environment" {
  type = string
}

variable "bot_locale" {
  type    = string
  default = "en_US"
}

variable "fulfillment_lambda_arn" {
  type = string
}

variable "lex_role_arn" {
  type = string
}

variable "idle_session_ttl_seconds" {
  type    = number
  default = 300
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Lex V2 Bot
resource "aws_lexv2models_bot" "airline_assistant" {
  name        = "${var.name_prefix}-bot"
  description = "Airline Assistant Chatbot for flight bookings, updates, and check-ins"
  role_arn    = var.lex_role_arn

  idle_session_ttl_in_seconds = var.idle_session_ttl_seconds

  data_privacy {
    child_directed = false
  }

  tags = {
    Name        = "${var.name_prefix}-bot"
    Environment = var.environment
  }
}

# Bot Locale
resource "aws_lexv2models_bot_locale" "en_us" {
  bot_id                           = aws_lexv2models_bot.airline_assistant.id
  bot_version                      = "DRAFT"
  locale_id                        = var.bot_locale
  n_lu_intent_confidence_threshold = 0.7

  voice_settings {
    voice_id = "Joanna"
    engine   = "neural"
  }
}

# Custom Slot Types
resource "aws_lexv2models_slot_type" "cabin_class" {
  bot_id      = aws_lexv2models_bot.airline_assistant.id
  bot_version = "DRAFT"
  locale_id   = var.bot_locale
  name        = "CabinClass"
  description = "Cabin class options"

  value_selection_setting {
    resolution_strategy = "OriginalValue"
  }

  slot_type_values {
    sample_value {
      value = "economy"
    }
    synonyms {
      value = "coach"
    }
    synonyms {
      value = "standard"
    }
  }

  slot_type_values {
    sample_value {
      value = "business"
    }
    synonyms {
      value = "business class"
    }
  }

  slot_type_values {
    sample_value {
      value = "first"
    }
    synonyms {
      value = "first class"
    }
  }

  depends_on = [aws_lexv2models_bot_locale.en_us]
}

resource "aws_lexv2models_slot_type" "update_type" {
  bot_id      = aws_lexv2models_bot.airline_assistant.id
  bot_version = "DRAFT"
  locale_id   = var.bot_locale
  name        = "UpdateType"
  description = "Booking update type options"

  value_selection_setting {
    resolution_strategy = "OriginalValue"
  }

  slot_type_values {
    sample_value {
      value = "date"
    }
    synonyms {
      value = "flight date"
    }
    synonyms {
      value = "departure date"
    }
  }

  slot_type_values {
    sample_value {
      value = "passengers"
    }
    synonyms {
      value = "travellers"
    }
    synonyms {
      value = "travelers"
    }
  }

  slot_type_values {
    sample_value {
      value = "seats"
    }
    synonyms {
      value = "seat assignment"
    }
  }

  slot_type_values {
    sample_value {
      value = "cabin"
    }
    synonyms {
      value = "cabin class"
    }
    synonyms {
      value = "class"
    }
  }

  depends_on = [aws_lexv2models_bot_locale.en_us]
}

resource "aws_lexv2models_slot_type" "seat_preference" {
  bot_id      = aws_lexv2models_bot.airline_assistant.id
  bot_version = "DRAFT"
  locale_id   = var.bot_locale
  name        = "SeatPreference"
  description = "Seat preference options"

  value_selection_setting {
    resolution_strategy = "OriginalValue"
  }

  slot_type_values {
    sample_value {
      value = "window"
    }
  }

  slot_type_values {
    sample_value {
      value = "middle"
    }
    synonyms {
      value = "center"
    }
  }

  slot_type_values {
    sample_value {
      value = "aisle"
    }
  }

  depends_on = [aws_lexv2models_bot_locale.en_us]
}

# BookFlight Intent
resource "aws_lexv2models_intent" "book_flight" {
  bot_id      = aws_lexv2models_bot.airline_assistant.id
  bot_version = "DRAFT"
  locale_id   = var.bot_locale
  name        = "BookFlight"
  description = "Intent to book a flight"

  sample_utterance {
    utterance = "I want to book a flight"
  }
  sample_utterance {
    utterance = "Book a flight"
  }
  sample_utterance {
    utterance = "Book me a flight from {Origin} to {Destination}"
  }
  sample_utterance {
    utterance = "I need tickets from {Origin} to {Destination}"
  }
  sample_utterance {
    utterance = "Find flights from {Origin} to {Destination} on {DepartureDate}"
  }
  sample_utterance {
    utterance = "I want to fly from {Origin} to {Destination}"
  }
  sample_utterance {
    utterance = "Book {Passengers} tickets to {Destination}"
  }

  fulfillment_code_hook {
    enabled = true
  }

  dialog_code_hook {
    enabled = true
  }

  depends_on = [
    aws_lexv2models_slot_type.cabin_class
  ]
}

# UpdateBooking Intent
resource "aws_lexv2models_intent" "update_booking" {
  bot_id      = aws_lexv2models_bot.airline_assistant.id
  bot_version = "DRAFT"
  locale_id   = var.bot_locale
  name        = "UpdateBooking"
  description = "Intent to update an existing booking"

  sample_utterance {
    utterance = "I want to change my booking"
  }
  sample_utterance {
    utterance = "Update my booking"
  }
  sample_utterance {
    utterance = "Change booking {BookingReference}"
  }
  sample_utterance {
    utterance = "Modify my reservation"
  }
  sample_utterance {
    utterance = "I need to change my flight date"
  }
  sample_utterance {
    utterance = "Update booking {BookingReference}"
  }

  fulfillment_code_hook {
    enabled = true
  }

  dialog_code_hook {
    enabled = true
  }

  depends_on = [
    aws_lexv2models_slot_type.update_type
  ]
}

# CheckIn Intent
resource "aws_lexv2models_intent" "check_in" {
  bot_id      = aws_lexv2models_bot.airline_assistant.id
  bot_version = "DRAFT"
  locale_id   = var.bot_locale
  name        = "CheckIn"
  description = "Intent to check in for a flight"

  sample_utterance {
    utterance = "I want to check in"
  }
  sample_utterance {
    utterance = "Check in for my flight"
  }
  sample_utterance {
    utterance = "Online check in"
  }
  sample_utterance {
    utterance = "Check in for booking {BookingReference}"
  }
  sample_utterance {
    utterance = "Web check in please"
  }
  sample_utterance {
    utterance = "I need to check in"
  }

  fulfillment_code_hook {
    enabled = true
  }

  dialog_code_hook {
    enabled = true
  }

  depends_on = [
    aws_lexv2models_slot_type.seat_preference
  ]
}

# Fallback Intent
resource "aws_lexv2models_intent" "fallback" {
  bot_id                = aws_lexv2models_bot.airline_assistant.id
  bot_version           = "DRAFT"
  locale_id             = var.bot_locale
  name                  = "FallbackIntent"
  description           = "Fallback intent for unrecognized utterances"
  parent_intent_signature = "AMAZON.FallbackIntent"

  depends_on = [aws_lexv2models_bot_locale.en_us]
}

# Bot Version
resource "aws_lexv2models_bot_version" "v1" {
  bot_id = aws_lexv2models_bot.airline_assistant.id

  locale_specification = {
    (var.bot_locale) = {
      source_bot_version = "DRAFT"
    }
  }

  depends_on = [
    aws_lexv2models_intent.book_flight,
    aws_lexv2models_intent.update_booking,
    aws_lexv2models_intent.check_in,
    aws_lexv2models_intent.fallback
  ]
}

# Bot Alias
resource "aws_lexv2models_bot_alias" "live" {
  bot_id      = aws_lexv2models_bot.airline_assistant.id
  bot_version = aws_lexv2models_bot_version.v1.bot_version
  name        = "${var.environment}-alias"
  description = "Live alias for ${var.environment} environment"

  bot_alias_locale_settings {
    locale_id = var.bot_locale

    bot_alias_locale_setting {
      enabled = true

      code_hook_specification {
        lambda_code_hook {
          lambda_arn                 = var.fulfillment_lambda_arn
          code_hook_interface_version = "1.0"
        }
      }
    }
  }

  conversation_log_settings {
    text_log_settings {
      enabled = true

      destination {
        cloudwatch {
          cloudwatch_log_group_arn = aws_cloudwatch_log_group.lex_conversations.arn
          log_prefix               = "lex-conversations"
        }
      }
    }
  }
}

# CloudWatch Log Group for Lex conversations
resource "aws_cloudwatch_log_group" "lex_conversations" {
  name              = "/aws/lex/${var.name_prefix}-bot"
  retention_in_days = var.environment == "prod" ? 90 : 30
}

output "bot_id" {
  value = aws_lexv2models_bot.airline_assistant.id
}

output "bot_alias_id" {
  value = aws_lexv2models_bot_alias.live.id
}

output "bot_version" {
  value = aws_lexv2models_bot_version.v1.bot_version
}
