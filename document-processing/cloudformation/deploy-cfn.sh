#!/bin/bash
set -e

STACK_NAME="${1:-ml-platform-dev}"
ENVIRONMENT="${2:-dev}"
AWS_REGION="${3:-eu-central-2}"

echo "ML Platform - CloudFormation Deployment"
echo "Stack: $STACK_NAME | Environment: $ENVIRONMENT | Region: $AWS_REGION"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TEMPLATE_BUCKET="cfn-templates-${ACCOUNT_ID}-${AWS_REGION}"

# Create S3 bucket for templates if it doesn't exist
aws s3 mb "s3://${TEMPLATE_BUCKET}" --region "$AWS_REGION" 2>/dev/null || true

# Upload nested templates to S3
echo "Uploading nested templates to S3..."
aws s3 sync ./nested "s3://${TEMPLATE_BUCKET}/${STACK_NAME}/nested" --delete

# Replace local template references with S3 URLs
echo "Preparing main template..."
sed "s|./nested/|https://${TEMPLATE_BUCKET}.s3.${AWS_REGION}.amazonaws.com/${STACK_NAME}/nested/|g" main.yaml > main-deployed.yaml

# Deploy the stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file main-deployed.yaml \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        ProjectName="ml-platform" \
    --tags \
        Project=ml-platform \
        Environment="$ENVIRONMENT" \
        ManagedBy=cloudformation

# Clean up
rm -f main-deployed.yaml

# Get outputs
echo ""
echo "Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

echo ""
echo "Deployment complete!"
