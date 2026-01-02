#!/bin/bash
set -e

# Configuration
STACK_NAME="${1:-call-sentiment-dev}"
ENVIRONMENT="${2:-dev}"
AWS_REGION="${3:-eu-central-2}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Call Sentiment Analysis - CloudFormation Deployment${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Stack Name: $STACK_NAME"
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account: $ACCOUNT_ID"
echo ""

# Create S3 bucket for nested templates if it doesn't exist
TEMPLATE_BUCKET="cfn-templates-${ACCOUNT_ID}-${AWS_REGION}"
if ! aws s3 ls "s3://${TEMPLATE_BUCKET}" 2>/dev/null; then
    echo -e "${YELLOW}Creating S3 bucket for templates: ${TEMPLATE_BUCKET}${NC}"
    aws s3 mb "s3://${TEMPLATE_BUCKET}" --region "$AWS_REGION"
fi

# Upload nested templates
echo -e "${YELLOW}Uploading nested templates to S3...${NC}"
aws s3 sync ./nested "s3://${TEMPLATE_BUCKET}/${STACK_NAME}/nested" --delete

# Get OpenSearch password (prompt if not set)
if [ -z "$OPENSEARCH_PASSWORD" ]; then
    echo -e "${YELLOW}Enter OpenSearch master password (min 8 chars):${NC}"
    read -s OPENSEARCH_PASSWORD
    echo ""
fi

# Deploy the stack
echo -e "${YELLOW}Deploying CloudFormation stack...${NC}"

# Replace template URLs in main.yaml
sed "s|./nested/|https://${TEMPLATE_BUCKET}.s3.${AWS_REGION}.amazonaws.com/${STACK_NAME}/nested/|g" main.yaml > main-deployed.yaml

aws cloudformation deploy \
    --template-file main-deployed.yaml \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        ProjectName="call-sentiment" \
        OpenSearchMasterPassword="$OPENSEARCH_PASSWORD" \
    --tags \
        Project=call-sentiment \
        Environment="$ENVIRONMENT" \
        ManagedBy=cloudformation

# Clean up
rm -f main-deployed.yaml

# Get outputs
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

echo ""
echo -e "${GREEN}Deployment successful!${NC}"
