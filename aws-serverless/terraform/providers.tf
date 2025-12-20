# =============================================================================
# Provider Configuration
# =============================================================================

# Provider configuration is in main.tf to allow variable interpolation
# This file is kept for backend configuration

terraform {
  # Uncomment for remote state
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "aws-serverless/terraform.tfstate"
  #   region         = "eu-central-2"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}
