#!/bin/bash
set -e

# Configuration
STACK_NAME="${1:-gps-tracking-dev}"
ENVIRONMENT="${2:-dev}"
AWS_REGION="${3:-eu-central-2}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}GPS Tracking System - CloudFormation Deployment${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Stack Name: $STACK_NAME"
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account: $ACCOUNT_ID"
echo ""

# Create S3 bucket for templates
TEMPLATE_BUCKET="cfn-templates-${ACCOUNT_ID}-${AWS_REGION}"
if ! aws s3 ls "s3://${TEMPLATE_BUCKET}" 2>/dev/null; then
    echo -e "${YELLOW}Creating S3 bucket for templates: ${TEMPLATE_BUCKET}${NC}"
    aws s3 mb "s3://${TEMPLATE_BUCKET}" --region "$AWS_REGION"
fi

# Upload nested templates
echo -e "${YELLOW}Uploading nested templates to S3...${NC}"
aws s3 sync ./nested "s3://${TEMPLATE_BUCKET}/${STACK_NAME}/nested" --delete

# Deploy
echo -e "${YELLOW}Deploying CloudFormation stack...${NC}"

sed "s|./nested/|https://${TEMPLATE_BUCKET}.s3.${AWS_REGION}.amazonaws.com/${STACK_NAME}/nested/|g" main.yaml > main-deployed.yaml

aws cloudformation deploy \
    --template-file main-deployed.yaml \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        ProjectName="gps-tracking" \
    --tags \
        Project=gps-tracking \
        Environment="$ENVIRONMENT" \
        ManagedBy=cloudformation

rm -f main-deployed.yaml

# Show outputs
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

echo ""
echo -e "${GREEN}Deployment successful!${NC}"
