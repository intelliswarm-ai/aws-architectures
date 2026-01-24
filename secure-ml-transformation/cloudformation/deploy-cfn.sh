#!/bin/bash
set -e

# Default values
ENVIRONMENT=${1:-dev}
REGION=${2:-eu-central-2}
PROJECT_NAME="secure-ml-transform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying Secure ML Transformation Stack${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"
echo "Project: ${PROJECT_NAME}"
echo ""

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account: ${ACCOUNT_ID}"

# S3 bucket for CloudFormation templates
CFN_BUCKET="${PROJECT_NAME}-cfn-${ACCOUNT_ID}-${REGION}"

# Check if CFN bucket exists, create if not
if ! aws s3 ls "s3://${CFN_BUCKET}" 2>&1 > /dev/null; then
    echo -e "${YELLOW}Creating CloudFormation template bucket: ${CFN_BUCKET}${NC}"
    aws s3 mb "s3://${CFN_BUCKET}" --region "${REGION}"
    aws s3api put-bucket-versioning \
        --bucket "${CFN_BUCKET}" \
        --versioning-configuration Status=Enabled
fi

# Upload nested templates
echo -e "${YELLOW}Uploading CloudFormation templates...${NC}"
aws s3 sync ./nested "s3://${CFN_BUCKET}/templates/nested/" --delete

# Upload main template
aws s3 cp ./main.yaml "s3://${CFN_BUCKET}/templates/main.yaml"

# Stack name
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# Check if stack exists
STACK_EXISTS=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" 2>&1 || true)

if echo "${STACK_EXISTS}" | grep -q "does not exist"; then
    echo -e "${YELLOW}Creating new stack: ${STACK_NAME}${NC}"
    ACTION="create-stack"
    WAIT_ACTION="stack-create-complete"
else
    echo -e "${YELLOW}Updating existing stack: ${STACK_NAME}${NC}"
    ACTION="update-stack"
    WAIT_ACTION="stack-update-complete"
fi

# Deploy stack
set +e
aws cloudformation ${ACTION} \
    --stack-name "${STACK_NAME}" \
    --template-url "https://${CFN_BUCKET}.s3.${REGION}.amazonaws.com/templates/main.yaml" \
    --parameters \
        ParameterKey=Environment,ParameterValue="${ENVIRONMENT}" \
        ParameterKey=ProjectName,ParameterValue="${PROJECT_NAME}" \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    --region "${REGION}" \
    --tags \
        Key=Project,Value="${PROJECT_NAME}" \
        Key=Environment,Value="${ENVIRONMENT}" \
        Key=ManagedBy,Value=CloudFormation

DEPLOY_RESULT=$?
set -e

if [ ${DEPLOY_RESULT} -ne 0 ]; then
    if [ "${ACTION}" = "update-stack" ]; then
        echo -e "${YELLOW}No updates to perform or update failed${NC}"
    else
        echo -e "${RED}Stack creation failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Waiting for stack ${ACTION} to complete...${NC}"
    aws cloudformation wait "${WAIT_ACTION}" \
        --stack-name "${STACK_NAME}" \
        --region "${REGION}"
fi

# Get stack outputs
echo -e "${GREEN}Stack deployment complete!${NC}"
echo ""
echo "Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

# Upload Glue scripts
echo ""
echo -e "${YELLOW}Uploading Glue scripts...${NC}"

SCRIPTS_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`ScriptsBucket`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -n "${SCRIPTS_BUCKET}" ]; then
    echo "Uploading to: s3://${SCRIPTS_BUCKET}/glue/jobs/"
    aws s3 sync ../glue/jobs/ "s3://${SCRIPTS_BUCKET}/glue/jobs/" --delete
    echo -e "${GREEN}Glue scripts uploaded successfully${NC}"
else
    echo -e "${YELLOW}Scripts bucket not found in outputs, skipping script upload${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
