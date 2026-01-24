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

echo -e "${RED}========================================${NC}"
echo -e "${RED}DESTROYING Secure ML Transformation${NC}"
echo -e "${RED}========================================${NC}"
echo ""
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"
echo "Method: ${DEPLOYMENT_METHOD}"
echo ""
echo -e "${RED}WARNING: This will destroy all resources!${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm) " -r
echo ""

if [[ $REPLY != "yes" ]]; then
    echo "Destruction cancelled"
    exit 0
fi

cd "$PROJECT_ROOT"

case $DEPLOYMENT_METHOD in
    terraform)
        echo -e "${YELLOW}Destroying with Terraform...${NC}"
        cd terraform

        # Select workspace
        terraform workspace select "${ENVIRONMENT}" 2>/dev/null || {
            echo "Workspace ${ENVIRONMENT} does not exist"
            exit 1
        }

        # Destroy
        terraform destroy \
            -var="environment=${ENVIRONMENT}" \
            -var="aws_region=${REGION}"
        ;;

    cloudformation)
        echo -e "${YELLOW}Destroying CloudFormation stack...${NC}"
        STACK_NAME="secure-ml-transform-${ENVIRONMENT}"

        aws cloudformation delete-stack \
            --stack-name "${STACK_NAME}" \
            --region "${REGION}"

        echo "Waiting for stack deletion..."
        aws cloudformation wait stack-delete-complete \
            --stack-name "${STACK_NAME}" \
            --region "${REGION}"
        ;;

    sam)
        echo -e "${YELLOW}Destroying SAM stack...${NC}"
        STACK_NAME="secure-ml-transform-lambda-${ENVIRONMENT}"

        sam delete \
            --stack-name "${STACK_NAME}" \
            --region "${REGION}" \
            --no-prompts
        ;;

    *)
        echo -e "${RED}Unknown deployment method: ${DEPLOYMENT_METHOD}${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Destruction complete!${NC}"
