#!/bin/bash
# Banking Platform - Deploy Script
# Deploys infrastructure and application to AWS

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
DIST_DIR="${PROJECT_ROOT}/dist"

# Default values
ENVIRONMENT="dev"
ACTION="apply"
AUTO_APPROVE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --destroy)
            ACTION="destroy"
            shift
            ;;
        --plan)
            ACTION="plan"
            shift
            ;;
        --auto-approve)
            AUTO_APPROVE="-auto-approve"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -e, --environment ENV  Environment to deploy (dev, staging, prod)"
            echo "  --plan                 Run terraform plan only"
            echo "  --destroy              Destroy infrastructure"
            echo "  --auto-approve         Auto-approve terraform apply"
            echo "  -h, --help             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=== Banking Platform Deploy ==="
echo "Environment: ${ENVIRONMENT}"
echo "Action: ${ACTION}"
echo ""

# Check if build artifacts exist
if [ ! -f "${DIST_DIR}/lambda.zip" ] || [ ! -f "${DIST_DIR}/app.zip" ]; then
    echo "Build artifacts not found. Running build..."
    "${SCRIPT_DIR}/build.sh"
fi

# Navigate to terraform directory
cd "${TERRAFORM_DIR}"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init -upgrade

# Select or create workspace
echo "Selecting workspace: ${ENVIRONMENT}"
terraform workspace select "${ENVIRONMENT}" 2>/dev/null || terraform workspace new "${ENVIRONMENT}"

# Run terraform action
case $ACTION in
    plan)
        echo "Running Terraform plan..."
        terraform plan -var="environment=${ENVIRONMENT}"
        ;;
    apply)
        echo "Running Terraform apply..."
        terraform apply -var="environment=${ENVIRONMENT}" ${AUTO_APPROVE}

        # Upload EC2 application to S3
        if [ -z "${AUTO_APPROVE}" ] || [ "${AUTO_APPROVE}" == "-auto-approve" ]; then
            echo ""
            echo "Uploading EC2 application to S3..."
            S3_BUCKET=$(terraform output -raw s3_bucket 2>/dev/null || echo "")
            if [ -n "${S3_BUCKET}" ]; then
                aws s3 cp "${DIST_DIR}/app.zip" "s3://${S3_BUCKET}/banking-processor/app.zip"
                echo "Application uploaded to s3://${S3_BUCKET}/banking-processor/app.zip"
            else
                echo "Warning: Could not determine S3 bucket. Manual upload required."
            fi
        fi

        echo ""
        echo "=== Deployment Complete ==="
        echo ""
        echo "Outputs:"
        terraform output
        ;;
    destroy)
        echo "Running Terraform destroy..."
        terraform destroy -var="environment=${ENVIRONMENT}" ${AUTO_APPROVE}
        echo ""
        echo "=== Infrastructure Destroyed ==="
        ;;
esac
