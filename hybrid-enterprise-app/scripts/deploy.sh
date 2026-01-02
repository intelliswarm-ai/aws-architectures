#!/bin/bash
# ============================================
# Deployment Script for Elastic Beanstalk
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_DIR="$PROJECT_ROOT/deploy"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# Default values
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-eu-central-2}"

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment   Environment (dev, staging, prod). Default: dev"
    echo "  -r, --region        AWS region. Default: eu-central-2"
    echo "  -b, --build         Build before deploying"
    echo "  -h, --help          Show this help message"
}

BUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "Deploying to Elastic Beanstalk"
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo "=========================================="

# Build if requested
if [[ "$BUILD" == "true" ]]; then
    echo "Building application..."
    "$SCRIPT_DIR/build.sh"
fi

# Find latest deployment bundle
BUNDLE=$(ls -t "$DEPLOY_DIR"/*.zip 2>/dev/null | head -1)
if [[ -z "$BUNDLE" ]]; then
    echo "ERROR: No deployment bundle found. Run build.sh first."
    exit 1
fi

echo "Using deployment bundle: $BUNDLE"

# Get application and environment names from Terraform
cd "$TERRAFORM_DIR"
APP_NAME=$(terraform output -raw application_name 2>/dev/null || echo "${ENVIRONMENT}-inventory-management")
ENV_NAME=$(terraform output -raw environment_name 2>/dev/null || echo "${ENVIRONMENT}-inventory-management-env")

# Upload to S3
S3_BUCKET="${ENVIRONMENT}-inventory-deployment-${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
VERSION_LABEL="v$(date +%Y%m%d%H%M%S)"
S3_KEY="deployments/${VERSION_LABEL}/$(basename "$BUNDLE")"

echo "Uploading to S3..."
aws s3 cp "$BUNDLE" "s3://${S3_BUCKET}/${S3_KEY}" --region "$AWS_REGION"

# Create application version
echo "Creating application version: $VERSION_LABEL"
aws elasticbeanstalk create-application-version \
    --application-name "$APP_NAME" \
    --version-label "$VERSION_LABEL" \
    --source-bundle S3Bucket="$S3_BUCKET",S3Key="$S3_KEY" \
    --region "$AWS_REGION"

# Update environment
echo "Updating environment: $ENV_NAME"
aws elasticbeanstalk update-environment \
    --environment-name "$ENV_NAME" \
    --version-label "$VERSION_LABEL" \
    --region "$AWS_REGION"

# Wait for deployment
echo "Waiting for deployment to complete..."
aws elasticbeanstalk wait environment-updated \
    --environment-name "$ENV_NAME" \
    --region "$AWS_REGION"

# Get application URL
APP_URL=$(aws elasticbeanstalk describe-environments \
    --environment-names "$ENV_NAME" \
    --query "Environments[0].CNAME" \
    --output text \
    --region "$AWS_REGION")

echo "=========================================="
echo "Deployment complete!"
echo "Application URL: http://$APP_URL"
echo "=========================================="
