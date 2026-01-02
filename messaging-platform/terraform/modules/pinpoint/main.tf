################################################################################
# Amazon Pinpoint Module
################################################################################

resource "aws_pinpoint_app" "sms_app" {
  name = "${var.project_name}-sms-app"

  tags = var.tags
}

# Configure SMS Channel
resource "aws_pinpoint_sms_channel" "sms" {
  application_id = aws_pinpoint_app.sms_app.application_id
  enabled        = true
}

# Event Stream to Kinesis
resource "aws_pinpoint_event_stream" "kinesis" {
  application_id         = aws_pinpoint_app.sms_app.application_id
  destination_stream_arn = var.kinesis_stream_arn
  role_arn               = var.kinesis_role_arn
}

# SMS Template for Welcome Message
resource "aws_pinpoint_sms_template" "welcome" {
  template_name = "${var.project_name}-welcome-sms"

  sms_template_request {
    body              = "Welcome to our service! Reply YES to confirm or STOP to unsubscribe."
    default_substitutions = jsonencode({})
    recommender_id    = null
  }

  tags = var.tags
}

# SMS Template for Confirmation Message
resource "aws_pinpoint_sms_template" "confirmation" {
  template_name = "${var.project_name}-confirmation-sms"

  sms_template_request {
    body              = "Thank you for confirming! You're now subscribed to our updates."
    default_substitutions = jsonencode({})
    recommender_id    = null
  }

  tags = var.tags
}

# SMS Template for Promotional Message
resource "aws_pinpoint_sms_template" "promotional" {
  template_name = "${var.project_name}-promo-sms"

  sms_template_request {
    body              = "Special offer just for you! Use code {{Attributes.promo_code}} for {{Attributes.discount}}% off. Reply STOP to opt out."
    default_substitutions = jsonencode({
      "Attributes.promo_code" = "WELCOME10"
      "Attributes.discount"   = "10"
    })
    recommender_id = null
  }

  tags = var.tags
}
