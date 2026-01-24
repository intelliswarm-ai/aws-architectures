#!/bin/bash
set -e

# ML Canary Deployment - CloudFormation Deployment Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
STACK_NAME="ml-canary-deployment"
ENVIRONMENT="dev"
AWS_REGION="${AWS_REGION:-eu-central-1}"
S3_BUCKET=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -n, --stack-name NAME     Stack name (default: ml-canary-deployment)"
    echo "  -e, --environment ENV     Environment (dev|staging|prod, default: dev)"
    echo "  -r, --region REGION       AWS region (default: eu-central-1)"
    echo "  -b, --bucket BUCKET       S3 bucket for templates (required)"
    echo "  -h, --help                Show this help message"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -b|--bucket)
            S3_BUCKET="$2"
            shift 2
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Validate S3 bucket
if [[ -z "$S3_BUCKET" ]]; then
    echo -e "${RED}Error: S3 bucket is required for nested templates${NC}"
    echo "Create a bucket and pass it with -b or --bucket"
    exit 1
fi

echo -e "${GREEN}ML Canary Deployment - CloudFormation Deployment${NC}"
echo "Stack Name: $STACK_NAME"
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo "Template Bucket: $S3_BUCKET"
echo ""

# Upload nested templates to S3
echo -e "${YELLOW}Uploading nested templates to S3...${NC}"
aws s3 sync "$SCRIPT_DIR/nested/" "s3://$S3_BUCKET/cloudformation/nested/" \
    --region "$AWS_REGION"

# Upload main template
aws s3 cp "$SCRIPT_DIR/main.yaml" "s3://$S3_BUCKET/cloudformation/main.yaml" \
    --region "$AWS_REGION"

# Build Lambda package if not exists
LAMBDA_ZIP="$PROJECT_ROOT/dist/lambda.zip"
if [[ ! -f "$LAMBDA_ZIP" ]]; then
    echo -e "${YELLOW}Building Lambda package...${NC}"
    "$PROJECT_ROOT/scripts/build.sh"
fi

# Upload Lambda package
echo -e "${YELLOW}Uploading Lambda package to S3...${NC}"
aws s3 cp "$LAMBDA_ZIP" "s3://$S3_BUCKET/lambda/lambda.zip" \
    --region "$AWS_REGION"

# Deploy CloudFormation stack
echo -e "${YELLOW}Deploying CloudFormation stack...${NC}"
aws cloudformation deploy \
    --template-url "https://$S3_BUCKET.s3.$AWS_REGION.amazonaws.com/cloudformation/main.yaml" \
    --stack-name "$STACK_NAME-$ENVIRONMENT" \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        ProjectName="$STACK_NAME" \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    --region "$AWS_REGION" \
    --tags \
        Project="$STACK_NAME" \
        Environment="$ENVIRONMENT" \
        ManagedBy=cloudformation

echo -e "${GREEN}Deployment complete!${NC}"

# Get outputs
echo ""
echo -e "${GREEN}Stack Outputs:${NC}"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME-$ENVIRONMENT" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table
