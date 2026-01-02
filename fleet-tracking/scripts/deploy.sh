#!/bin/bash
# GPS Tracking System - Deployment Script
# Deploys infrastructure using Terraform

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"

# Default values
ENVIRONMENT="${ENVIRONMENT:-dev}"
AUTO_APPROVE="${AUTO_APPROVE:-false}"

echo "=== GPS Tracking System Deployment ==="
echo "Environment: ${ENVIRONMENT}"
echo "Terraform directory: ${TERRAFORM_DIR}"

# Build Lambda package first
echo ""
echo "Building Lambda package..."
"${SCRIPT_DIR}/build.sh"

# Navigate to Terraform directory
cd "${TERRAFORM_DIR}"

# Initialize Terraform
echo ""
echo "Initializing Terraform..."
terraform init -upgrade

# Validate configuration
echo ""
echo "Validating Terraform configuration..."
terraform validate

# Plan deployment
echo ""
echo "Planning deployment..."
terraform plan \
    -var="environment=${ENVIRONMENT}" \
    -var-file="terraform.tfvars" \
    -out=tfplan

# Apply if auto-approve or user confirms
if [ "${AUTO_APPROVE}" = "true" ]; then
    echo ""
    echo "Applying changes (auto-approved)..."
    terraform apply tfplan
else
    echo ""
    read -p "Apply these changes? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        terraform apply tfplan
    else
        echo "Deployment cancelled."
        rm -f tfplan
        exit 0
    fi
fi

# Clean up plan file
rm -f tfplan

# Show outputs
echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Outputs:"
terraform output

echo ""
echo "Useful commands:"
echo "  - Invoke producer: aws lambda invoke --function-name \$(terraform output -raw producer_function_name) --payload '{}' response.json"
echo "  - View truck positions: aws dynamodb scan --table-name \$(terraform output -raw positions_table_name)"
echo "  - View Kinesis stream: aws kinesis describe-stream --stream-name \$(terraform output -raw kinesis_stream_name)"
