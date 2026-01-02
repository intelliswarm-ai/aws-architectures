#!/bin/bash
# SMS Marketing System - Deploy Script
# Deploys infrastructure and Lambda functions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
DIST_DIR="${PROJECT_ROOT}/dist"

# Default values
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-eu-central-2}"

echo "=== SMS Marketing System Deployment ==="
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${AWS_REGION}"
echo ""

# Build Lambda package first
echo "Building Lambda package..."
"${SCRIPT_DIR}/build.sh"

# Check if lambda.zip exists
if [ ! -f "${DIST_DIR}/lambda.zip" ]; then
    echo "Error: Lambda package not found. Run build.sh first."
    exit 1
fi

# Initialize Terraform
echo ""
echo "Initializing Terraform..."
cd "${TERRAFORM_DIR}"
terraform init

# Validate Terraform configuration
echo ""
echo "Validating Terraform configuration..."
terraform validate

# Plan deployment
echo ""
echo "Planning deployment..."
terraform plan \
    -var-file="terraform.tfvars" \
    -var="environment=${ENVIRONMENT}" \
    -out=tfplan

# Ask for confirmation
read -p "Do you want to apply this plan? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Apply deployment
echo ""
echo "Applying deployment..."
terraform apply tfplan

# Clean up plan file
rm -f tfplan

# Get outputs
echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Outputs:"
terraform output

echo ""
echo "Next steps:"
echo "1. Configure Pinpoint SMS channel in the AWS Console"
echo "2. Request a dedicated number or sender ID"
echo "3. Create segments and journeys in Pinpoint"
echo "4. Test SMS sending with the API"
