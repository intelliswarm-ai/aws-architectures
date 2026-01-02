#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
ENVIRONMENT="dev"
AWS_REGION="eu-central-2"
STACK_NAME=""
ACTION="deploy"
S3_BUCKET=""
ALARM_EMAIL=""
WAIT=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -e, --environment    Environment name (dev, staging, prod). Default: dev"
    echo "  -r, --region         AWS region. Default: eu-central-2"
    echo "  -s, --stack-name     CloudFormation stack name. Default: airline-chatbot-{env}"
    echo "  -b, --s3-bucket      S3 bucket for Lambda code and nested templates"
    echo "  --alarm-email        Email for alarm notifications"
    echo "  --delete             Delete the stack instead of deploy"
    echo "  --no-wait            Don't wait for stack operations to complete"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -e dev -b my-deployment-bucket"
    echo "  $0 -e prod -b my-deployment-bucket --alarm-email alerts@company.com"
    echo "  $0 -e dev --delete"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
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
        -s|--stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        -b|--s3-bucket)
            S3_BUCKET="$2"
            shift 2
            ;;
        --alarm-email)
            ALARM_EMAIL="$2"
            shift 2
            ;;
        --delete)
            ACTION="delete"
            shift
            ;;
        --no-wait)
            WAIT=false
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Set default stack name if not provided
if [ -z "$STACK_NAME" ]; then
    STACK_NAME="airline-chatbot-${ENVIRONMENT}"
fi

log_info "Environment: $ENVIRONMENT"
log_info "Region: $AWS_REGION"
log_info "Stack Name: $STACK_NAME"

# Delete stack
if [ "$ACTION" == "delete" ]; then
    log_info "Deleting CloudFormation stack..."
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"

    if [ "$WAIT" == true ]; then
        log_info "Waiting for stack deletion to complete..."
        aws cloudformation wait stack-delete-complete \
            --stack-name "$STACK_NAME" \
            --region "$AWS_REGION"
        log_info "Stack deleted successfully!"
    else
        log_info "Stack deletion initiated. Use 'aws cloudformation describe-stacks' to check status."
    fi
    exit 0
fi

# Check for S3 bucket
if [ -z "$S3_BUCKET" ]; then
    log_error "S3 bucket is required for deployment. Use -b or --s3-bucket option."
    log_info "The S3 bucket is needed to store nested CloudFormation templates and Lambda code."
    exit 1
fi

# Build Lambda package
log_info "Building Lambda package..."
"$PROJECT_DIR/scripts/build.sh"

# Upload Lambda code to S3
LAMBDA_S3_KEY="cloudformation/${STACK_NAME}/lambda.zip"
log_info "Uploading Lambda code to s3://${S3_BUCKET}/${LAMBDA_S3_KEY}..."
aws s3 cp "$PROJECT_DIR/build/lambda.zip" "s3://${S3_BUCKET}/${LAMBDA_S3_KEY}" --region "$AWS_REGION"

# Package nested templates
log_info "Packaging CloudFormation templates..."
PACKAGED_TEMPLATE="$SCRIPT_DIR/packaged.yaml"

aws cloudformation package \
    --template-file "$SCRIPT_DIR/main.yaml" \
    --s3-bucket "$S3_BUCKET" \
    --s3-prefix "cloudformation/${STACK_NAME}/templates" \
    --output-template-file "$PACKAGED_TEMPLATE" \
    --region "$AWS_REGION"

# Deploy stack
log_info "Deploying CloudFormation stack..."

PARAMETERS="ParameterKey=Environment,ParameterValue=${ENVIRONMENT}"
PARAMETERS="${PARAMETERS} ParameterKey=LambdaS3Bucket,ParameterValue=${S3_BUCKET}"
PARAMETERS="${PARAMETERS} ParameterKey=LambdaS3Key,ParameterValue=${LAMBDA_S3_KEY}"

if [ -n "$ALARM_EMAIL" ]; then
    PARAMETERS="${PARAMETERS} ParameterKey=AlarmEmail,ParameterValue=${ALARM_EMAIL}"
fi

aws cloudformation deploy \
    --template-file "$PACKAGED_TEMPLATE" \
    --stack-name "$STACK_NAME" \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    --parameter-overrides $PARAMETERS \
    --region "$AWS_REGION" \
    --no-fail-on-empty-changeset

# Get outputs
log_info "Stack deployment complete! Outputs:"
echo ""
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

# Clean up packaged template
rm -f "$PACKAGED_TEMPLATE"

echo ""
log_info "Deployment complete!"
log_info "Test the bot with the AWS CLI command shown in the outputs above."
