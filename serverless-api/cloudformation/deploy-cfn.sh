#!/bin/bash
set -e

STACK_NAME="${1:-task-automation-dev}"
ENVIRONMENT="${2:-dev}"
AWS_REGION="${3:-eu-central-2}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Task Automation System - CloudFormation Deployment${NC}"
echo "Stack: $STACK_NAME | Environment: $ENVIRONMENT | Region: $AWS_REGION"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TEMPLATE_BUCKET="cfn-templates-${ACCOUNT_ID}-${AWS_REGION}"

aws s3 mb "s3://${TEMPLATE_BUCKET}" --region "$AWS_REGION" 2>/dev/null || true
aws s3 sync ./nested "s3://${TEMPLATE_BUCKET}/${STACK_NAME}/nested" --delete

sed "s|./nested/|https://${TEMPLATE_BUCKET}.s3.${AWS_REGION}.amazonaws.com/${STACK_NAME}/nested/|g" main.yaml > main-deployed.yaml

aws cloudformation deploy \
    --template-file main-deployed.yaml \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides Environment="$ENVIRONMENT" ProjectName="task-automation"

rm -f main-deployed.yaml

echo -e "${GREEN}Deployment complete!${NC}"
aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' --output table
