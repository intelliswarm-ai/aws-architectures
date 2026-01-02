# =============================================================================
# WAF Module - Web Application Firewall
# =============================================================================

locals {
  prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Module      = "waf"
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# IP Sets
# -----------------------------------------------------------------------------
resource "aws_wafv2_ip_set" "allowed" {
  count = length(var.allowed_ip_addresses) > 0 ? 1 : 0

  name               = "${local.prefix}-allowed-ips"
  scope              = var.scope
  ip_address_version = "IPV4"
  addresses          = var.allowed_ip_addresses

  tags = local.common_tags
}

resource "aws_wafv2_ip_set" "blocked" {
  count = length(var.blocked_ip_addresses) > 0 ? 1 : 0

  name               = "${local.prefix}-blocked-ips"
  scope              = var.scope
  ip_address_version = "IPV4"
  addresses          = var.blocked_ip_addresses

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Web ACL
# -----------------------------------------------------------------------------
resource "aws_wafv2_web_acl" "this" {
  name        = "${local.prefix}-waf"
  description = "WAF for ${var.project_name} ${var.environment}"
  scope       = var.scope

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${replace(local.prefix, "-", "")}WAF"
    sampled_requests_enabled   = true
  }

  # Priority counter
  # 1-10: IP-based rules
  # 11-20: Geo rules
  # 21-30: Rate limiting
  # 31-100: AWS Managed Rules

  # -----------------------------------------------------------------------------
  # IP Allow List (Priority 1)
  # -----------------------------------------------------------------------------
  dynamic "rule" {
    for_each = length(var.allowed_ip_addresses) > 0 ? [1] : []
    content {
      name     = "AllowListedIPs"
      priority = 1

      override_action {
        none {}
      }

      statement {
        ip_set_reference_statement {
          arn = aws_wafv2_ip_set.allowed[0].arn
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "AllowListedIPs"
        sampled_requests_enabled   = true
      }
    }
  }

  # -----------------------------------------------------------------------------
  # IP Block List (Priority 2)
  # -----------------------------------------------------------------------------
  dynamic "rule" {
    for_each = length(var.blocked_ip_addresses) > 0 ? [1] : []
    content {
      name     = "BlockListedIPs"
      priority = 2

      action {
        block {}
      }

      statement {
        ip_set_reference_statement {
          arn = aws_wafv2_ip_set.blocked[0].arn
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "BlockListedIPs"
        sampled_requests_enabled   = true
      }
    }
  }

  # -----------------------------------------------------------------------------
  # Geo Blocking (Priority 11-12)
  # -----------------------------------------------------------------------------
  dynamic "rule" {
    for_each = var.enable_geo_blocking && length(var.blocked_countries) > 0 ? [1] : []
    content {
      name     = "BlockedCountries"
      priority = 11

      action {
        block {}
      }

      statement {
        geo_match_statement {
          country_codes = var.blocked_countries
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "BlockedCountries"
        sampled_requests_enabled   = true
      }
    }
  }

  dynamic "rule" {
    for_each = var.enable_geo_blocking && length(var.allowed_countries) > 0 ? [1] : []
    content {
      name     = "AllowedCountriesOnly"
      priority = 12

      action {
        block {}
      }

      statement {
        not_statement {
          statement {
            geo_match_statement {
              country_codes = var.allowed_countries
            }
          }
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "AllowedCountriesOnly"
        sampled_requests_enabled   = true
      }
    }
  }

  # -----------------------------------------------------------------------------
  # Rate Limiting (Priority 21)
  # -----------------------------------------------------------------------------
  rule {
    name     = "RateLimit"
    priority = 21

    action {
      dynamic "block" {
        for_each = var.rate_limit_action == "block" ? [1] : []
        content {}
      }
      dynamic "count" {
        for_each = var.rate_limit_action == "count" ? [1] : []
        content {}
      }
    }

    statement {
      rate_based_statement {
        limit              = var.rate_limit
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit"
      sampled_requests_enabled   = true
    }
  }

  # -----------------------------------------------------------------------------
  # AWS Managed Rules - Common Rule Set (Priority 31)
  # -----------------------------------------------------------------------------
  dynamic "rule" {
    for_each = var.enable_common_rules ? [1] : []
    content {
      name     = "AWSManagedRulesCommonRuleSet"
      priority = 31

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          vendor_name = "AWS"
          name        = "AWSManagedRulesCommonRuleSet"

          rule_action_override {
            name = "SizeRestrictions_BODY"
            action_to_use {
              count {}
            }
          }
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "AWSManagedRulesCommonRuleSet"
        sampled_requests_enabled   = true
      }
    }
  }

  # -----------------------------------------------------------------------------
  # AWS Managed Rules - SQL Injection (Priority 32)
  # -----------------------------------------------------------------------------
  dynamic "rule" {
    for_each = var.enable_sqli_rules ? [1] : []
    content {
      name     = "AWSManagedRulesSQLiRuleSet"
      priority = 32

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          vendor_name = "AWS"
          name        = "AWSManagedRulesSQLiRuleSet"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "AWSManagedRulesSQLiRuleSet"
        sampled_requests_enabled   = true
      }
    }
  }

  # -----------------------------------------------------------------------------
  # AWS Managed Rules - Known Bad Inputs (Priority 33)
  # -----------------------------------------------------------------------------
  dynamic "rule" {
    for_each = var.enable_known_bad_inputs ? [1] : []
    content {
      name     = "AWSManagedRulesKnownBadInputsRuleSet"
      priority = 33

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          vendor_name = "AWS"
          name        = "AWSManagedRulesKnownBadInputsRuleSet"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "AWSManagedRulesKnownBadInputsRuleSet"
        sampled_requests_enabled   = true
      }
    }
  }

  # -----------------------------------------------------------------------------
  # AWS Managed Rules - IP Reputation (Priority 34)
  # -----------------------------------------------------------------------------
  dynamic "rule" {
    for_each = var.enable_ip_reputation ? [1] : []
    content {
      name     = "AWSManagedRulesAmazonIpReputationList"
      priority = 34

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          vendor_name = "AWS"
          name        = "AWSManagedRulesAmazonIpReputationList"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "AWSManagedRulesAmazonIpReputationList"
        sampled_requests_enabled   = true
      }
    }
  }

  # -----------------------------------------------------------------------------
  # AWS Managed Rules - Anonymous IP (Priority 35)
  # -----------------------------------------------------------------------------
  dynamic "rule" {
    for_each = var.enable_anonymous_ip ? [1] : []
    content {
      name     = "AWSManagedRulesAnonymousIpList"
      priority = 35

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          vendor_name = "AWS"
          name        = "AWSManagedRulesAnonymousIpList"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "AWSManagedRulesAnonymousIpList"
        sampled_requests_enabled   = true
      }
    }
  }

  # -----------------------------------------------------------------------------
  # AWS Managed Rules - Bot Control (Priority 36) - Additional Cost
  # -----------------------------------------------------------------------------
  dynamic "rule" {
    for_each = var.enable_bot_control ? [1] : []
    content {
      name     = "AWSManagedRulesBotControlRuleSet"
      priority = 36

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          vendor_name = "AWS"
          name        = "AWSManagedRulesBotControlRuleSet"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "AWSManagedRulesBotControlRuleSet"
        sampled_requests_enabled   = true
      }
    }
  }

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# WAF Logging
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "waf" {
  count = var.enable_logging ? 1 : 0

  name              = "aws-waf-logs-${local.prefix}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_wafv2_web_acl_logging_configuration" "this" {
  count = var.enable_logging ? 1 : 0

  log_destination_configs = [aws_cloudwatch_log_group.waf[0].arn]
  resource_arn            = aws_wafv2_web_acl.this.arn

  logging_filter {
    default_behavior = "KEEP"

    filter {
      behavior = "KEEP"

      condition {
        action_condition {
          action = "BLOCK"
        }
      }

      requirement = "MEETS_ANY"
    }
  }
}
