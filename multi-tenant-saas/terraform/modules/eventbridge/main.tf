# =============================================================================
# EventBridge Module
# =============================================================================

resource "aws_cloudwatch_event_bus" "main" {
  name = "${var.name_prefix}-bus"
  tags = var.tags
}
