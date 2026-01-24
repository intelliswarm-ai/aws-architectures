#!/bin/bash
set -e

# Default values
ENVIRONMENT=${1:-dev}
REGION=${2:-eu-central-2}
DEPLOYMENT_METHOD=${3:-terraform}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying Secure ML Transformation${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"
echo "Method: ${DEPLOYMENT_METHOD}"
echo ""

cd "$PROJECT_ROOT"

case $DEPLOYMENT_METHOD in
    terraform)
        echo -e "${YELLOW}Deploying with Terraform...${NC}"
        cd terraform

        # Initialize Terraform
        terraform init

        # Create workspace if it doesn't exist
        terraform workspace select "${ENVIRONMENT}" 2>/dev/null || terraform workspace new "${ENVIRONMENT}"

        # Plan and apply
        terraform plan \
            -var="environment=${ENVIRONMENT}" \
            -var="aws_region=${REGION}" \
            -out=tfplan

        echo ""
        read -p "Apply this plan? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            terraform apply tfplan
        else
            echo "Deployment cancelled"
            exit 0
        fi

        # Upload Glue scripts
        echo -e "${YELLOW}Uploading Glue scripts...${NC}"
        SCRIPTS_BUCKET=$(terraform output -raw scripts_bucket 2>/dev/null || echo "")
        if [ -n "$SCRIPTS_BUCKET" ]; then
            aws s3 sync ../glue/jobs/ "s3://${SCRIPTS_BUCKET}/glue/jobs/" --delete
            echo -e "${GREEN}Glue scripts uploaded successfully${NC}"
        fi
        ;;

    cloudformation)
        echo -e "${YELLOW}Deploying with CloudFormation...${NC}"
        cd cloudformation
        chmod +x deploy-cfn.sh
        ./deploy-cfn.sh "${ENVIRONMENT}" "${REGION}"
        ;;

    sam)
        echo -e "${YELLOW}Deploying with SAM...${NC}"
        cd sam
        sam build
        sam deploy --config-env "${ENVIRONMENT}" --region "${REGION}"
        ;;

    *)
        echo -e "${RED}Unknown deployment method: ${DEPLOYMENT_METHOD}${NC}"
        echo "Usage: $0 <environment> <region> <terraform|cloudformation|sam>"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
