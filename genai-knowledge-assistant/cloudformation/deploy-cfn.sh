#!/bin/bash
set -euo pipefail

# GenAI Knowledge Assistant - CloudFormation Deployment Script
# This script packages and deploys the CloudFormation nested stacks

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-eu-central-2}"
PROJECT_NAME="${PROJECT_NAME:-genai-assistant}"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -p|--project)
            PROJECT_NAME="$2"
            STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
            shift 2
            ;;
        --destroy)
            DESTROY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -e, --environment ENV    Environment (dev, staging, prod) [default: dev]"
            echo "  -r, --region REGION      AWS region [default: eu-central-2]"
            echo "  -p, --project NAME       Project name [default: genai-assistant]"
            echo "  --destroy                Destroy the stack"
            echo "  -h, --help               Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create S3 bucket for templates if it doesn't exist
create_template_bucket() {
    local bucket_name="${PROJECT_NAME}-${ENVIRONMENT}-cfn-templates-${AWS_ACCOUNT_ID}"

    if ! aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        log_info "Creating S3 bucket for templates: $bucket_name"
        if [ "$AWS_REGION" == "us-east-1" ]; then
            aws s3api create-bucket --bucket "$bucket_name" --region "$AWS_REGION"
        else
            aws s3api create-bucket --bucket "$bucket_name" --region "$AWS_REGION" \
                --create-bucket-configuration LocationConstraint="$AWS_REGION"
        fi

        # Enable versioning
        aws s3api put-bucket-versioning --bucket "$bucket_name" \
            --versioning-configuration Status=Enabled

        # Block public access
        aws s3api put-public-access-block --bucket "$bucket_name" \
            --public-access-block-configuration \
            "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    fi

    echo "$bucket_name"
}

# Upload nested templates to S3
upload_templates() {
    local bucket_name="$1"
    local templates_dir="${SCRIPT_DIR}/nested"

    log_info "Uploading nested templates to s3://${bucket_name}/cloudformation/nested/"

    for template in "$templates_dir"/*.yaml; do
        if [ -f "$template" ]; then
            local filename=$(basename "$template")
            aws s3 cp "$template" "s3://${bucket_name}/cloudformation/nested/${filename}" \
                --region "$AWS_REGION"
            log_info "  Uploaded: $filename"
        fi
    done
}

# Build Lambda package
build_lambda() {
    log_info "Building Lambda package..."

    if [ -f "${PROJECT_DIR}/scripts/build.sh" ]; then
        bash "${PROJECT_DIR}/scripts/build.sh"
    else
        log_warn "build.sh not found, skipping Lambda build"
    fi
}

# Deploy CloudFormation stack
deploy_stack() {
    local bucket_name="$1"

    log_info "Deploying CloudFormation stack: $STACK_NAME"

    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" 2>/dev/null; then
        log_info "Updating existing stack..."
        local action="update-stack"
        local wait_action="stack-update-complete"
    else
        log_info "Creating new stack..."
        local action="create-stack"
        local wait_action="stack-create-complete"
    fi

    # Deploy
    aws cloudformation $action \
        --stack-name "$STACK_NAME" \
        --template-body "file://${SCRIPT_DIR}/main.yaml" \
        --parameters \
            ParameterKey=ProjectName,ParameterValue="$PROJECT_NAME" \
            ParameterKey=Environment,ParameterValue="$ENVIRONMENT" \
            ParameterKey=TemplatesBucket,ParameterValue="$bucket_name" \
            ParameterKey=TemplatesPrefix,ParameterValue="cloudformation/nested" \
        --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
        --region "$AWS_REGION" \
        --tags \
            Key=Project,Value="$PROJECT_NAME" \
            Key=Environment,Value="$ENVIRONMENT" \
        || {
            # If no changes, that's okay
            if [ "$action" == "update-stack" ]; then
                log_warn "No updates to perform (stack is up to date)"
                return 0
            else
                return 1
            fi
        }

    log_info "Waiting for stack operation to complete..."
    aws cloudformation wait $wait_action \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"

    log_info "Stack operation completed successfully"
}

# Destroy stack
destroy_stack() {
    log_info "Destroying CloudFormation stack: $STACK_NAME"

    # Check if stack exists
    if ! aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" 2>/dev/null; then
        log_warn "Stack $STACK_NAME does not exist"
        return 0
    fi

    # Confirm destruction
    echo -e "${YELLOW}WARNING: This will destroy all resources in stack $STACK_NAME${NC}"
    read -p "Are you sure you want to continue? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Destruction cancelled"
        exit 0
    fi

    # Delete stack
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"

    log_info "Waiting for stack deletion to complete..."
    aws cloudformation wait stack-delete-complete \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"

    log_info "Stack deleted successfully"
}

# Print stack outputs
print_outputs() {
    log_info "Stack Outputs:"

    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table
}

# Main execution
main() {
    log_info "GenAI Knowledge Assistant - CloudFormation Deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Region: $AWS_REGION"
    log_info "Project: $PROJECT_NAME"
    log_info "Stack: $STACK_NAME"
    echo ""

    # Get AWS Account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    log_info "AWS Account: $AWS_ACCOUNT_ID"

    # Handle destroy
    if [ "${DESTROY:-false}" == "true" ]; then
        destroy_stack
        exit 0
    fi

    # Create template bucket
    TEMPLATE_BUCKET=$(create_template_bucket)
    log_info "Templates bucket: $TEMPLATE_BUCKET"

    # Upload nested templates
    upload_templates "$TEMPLATE_BUCKET"

    # Build Lambda
    build_lambda

    # Deploy stack
    deploy_stack "$TEMPLATE_BUCKET"

    # Print outputs
    print_outputs

    echo ""
    log_info "Deployment completed successfully!"
}

main
