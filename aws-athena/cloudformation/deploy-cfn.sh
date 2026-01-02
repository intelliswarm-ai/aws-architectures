#!/bin/bash
set -euo pipefail

# CloudFormation deployment script for AWS Athena Data Lake

# Configuration
PROJECT_NAME="${PROJECT_NAME:-athena-datalake}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-eu-central-2}"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
CFN_BUCKET="${AWS_ACCOUNT_ID}-cfn-templates"

log_info "Deploying ${STACK_NAME} to ${AWS_REGION}"
log_info "Account: ${AWS_ACCOUNT_ID}"

# Create S3 bucket for templates if it doesn't exist
if ! aws s3api head-bucket --bucket "${CFN_BUCKET}" 2>/dev/null; then
    log_info "Creating S3 bucket for CloudFormation templates: ${CFN_BUCKET}"
    aws s3api create-bucket \
        --bucket "${CFN_BUCKET}" \
        --region "${AWS_REGION}" \
        --create-bucket-configuration LocationConstraint="${AWS_REGION}"
fi

# Upload nested templates
log_info "Uploading CloudFormation templates to S3..."
aws s3 sync ./nested/ "s3://${CFN_BUCKET}/aws-athena/nested/" --delete

# Upload main template
aws s3 cp ./main.yaml "s3://${CFN_BUCKET}/aws-athena/main.yaml"

# Build and upload Lambda code
log_info "Building and uploading Lambda packages..."
cd ..

# Create dist directory
mkdir -p dist

# Package Lambda functions
for handler in ingest etl query api; do
    log_info "Packaging ${handler} handler..."
    cd src
    zip -r "../dist/${handler}.zip" . -x "*.pyc" -x "__pycache__/*" -x "*.egg-info/*"
    cd ..
done

# Create Lambda layer (dependencies)
log_info "Creating Lambda layer..."
pip install -r requirements.txt -t dist/python/
cd dist
zip -r layer.zip python/
cd ..

# Upload Lambda packages
RESULTS_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-results-${AWS_ACCOUNT_ID}"

# Create results bucket if needed
if aws s3api head-bucket --bucket "${RESULTS_BUCKET}" 2>/dev/null; then
    log_info "Uploading Lambda packages to ${RESULTS_BUCKET}..."
    aws s3 cp dist/layer.zip "s3://${RESULTS_BUCKET}/lambda/layer.zip"
    for handler in ingest etl query api; do
        aws s3 cp "dist/${handler}.zip" "s3://${RESULTS_BUCKET}/lambda/${handler}.zip"
    done
else
    log_warn "Results bucket ${RESULTS_BUCKET} does not exist. It will be created by the stack."
    log_warn "After stack creation, re-run this script to upload Lambda packages."
fi

# Upload Glue ETL script
if aws s3api head-bucket --bucket "${RESULTS_BUCKET}" 2>/dev/null; then
    log_info "Uploading Glue ETL script..."
    aws s3 cp glue/etl_job.py "s3://${RESULTS_BUCKET}/glue-scripts/etl_job.py"
fi

cd cloudformation

# Deploy or update stack
if aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region "${AWS_REGION}" 2>/dev/null; then
    log_info "Updating existing stack: ${STACK_NAME}"
    ACTION="update-stack"
else
    log_info "Creating new stack: ${STACK_NAME}"
    ACTION="create-stack"
fi

aws cloudformation ${ACTION} \
    --stack-name "${STACK_NAME}" \
    --template-url "https://${CFN_BUCKET}.s3.${AWS_REGION}.amazonaws.com/aws-athena/main.yaml" \
    --parameters \
        ParameterKey=ProjectName,ParameterValue="${PROJECT_NAME}" \
        ParameterKey=Environment,ParameterValue="${ENVIRONMENT}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "${AWS_REGION}" \
    --tags \
        Key=Project,Value="${PROJECT_NAME}" \
        Key=Environment,Value="${ENVIRONMENT}" \
        Key=ManagedBy,Value=cloudformation

# Wait for stack operation to complete
log_info "Waiting for stack operation to complete..."
if [ "${ACTION}" == "create-stack" ]; then
    aws cloudformation wait stack-create-complete \
        --stack-name "${STACK_NAME}" \
        --region "${AWS_REGION}"
else
    aws cloudformation wait stack-update-complete \
        --stack-name "${STACK_NAME}" \
        --region "${AWS_REGION}"
fi

# Print outputs
log_info "Stack deployment complete!"
log_info ""
log_info "Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${AWS_REGION}" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

log_info ""
log_info "Deployment successful!"
