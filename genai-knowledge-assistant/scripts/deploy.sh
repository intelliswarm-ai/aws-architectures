#!/bin/bash
# =============================================================================
# Deploy Script - GenAI Knowledge Assistant (Terraform)
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_DIR/terraform"

# Default values
ENVIRONMENT="dev"
SKIP_BUILD=false
AUTO_APPROVE=false
DESTROY=false
PLAN_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        --destroy)
            DESTROY=true
            shift
            ;;
        --plan)
            PLAN_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -e, --env ENV      Environment (dev, staging, prod) [default: dev]"
            echo "  --skip-build       Skip building Lambda package"
            echo "  --auto-approve     Auto-approve Terraform changes"
            echo "  --destroy          Destroy infrastructure"
            echo "  --plan             Plan only, don't apply"
            echo "  -h, --help         Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying GenAI Knowledge Assistant${NC}"
echo -e "${GREEN}Environment: $ENVIRONMENT${NC}"
echo -e "${GREEN}========================================${NC}"

# Build Lambda package
if [ "$SKIP_BUILD" = false ] && [ "$DESTROY" = false ]; then
    echo -e "\n${YELLOW}Building Lambda package...${NC}"
    "$SCRIPT_DIR/build.sh"
fi

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: Terraform is required${NC}"
    exit 1
fi

cd "$TERRAFORM_DIR"

# Initialize Terraform
echo -e "\n${YELLOW}Initializing Terraform...${NC}"
terraform init -upgrade

# Validate configuration
echo -e "\n${YELLOW}Validating configuration...${NC}"
terraform validate

# Set tfvars file
TFVARS_FILE="terraform.tfvars"
if [ -f "environments/${ENVIRONMENT}.tfvars" ]; then
    TFVARS_FILE="environments/${ENVIRONMENT}.tfvars"
fi

# Plan
echo -e "\n${YELLOW}Planning changes...${NC}"
PLAN_ARGS="-var-file=$TFVARS_FILE -var environment=$ENVIRONMENT"

if [ "$DESTROY" = true ]; then
    terraform plan $PLAN_ARGS -destroy -out=tfplan
else
    terraform plan $PLAN_ARGS -out=tfplan
fi

# Exit if plan only
if [ "$PLAN_ONLY" = true ]; then
    echo -e "\n${GREEN}Plan complete. Review above changes.${NC}"
    exit 0
fi

# Apply
if [ "$AUTO_APPROVE" = true ]; then
    echo -e "\n${YELLOW}Applying changes (auto-approved)...${NC}"
    terraform apply tfplan
else
    echo -e "\n${YELLOW}Do you want to apply these changes?${NC}"
    read -p "Enter 'yes' to apply: " CONFIRM
    if [ "$CONFIRM" = "yes" ]; then
        terraform apply tfplan
    else
        echo -e "${YELLOW}Cancelled.${NC}"
        rm -f tfplan
        exit 0
    fi
fi

rm -f tfplan

# Show outputs
if [ "$DESTROY" = false ]; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    terraform output -json | python3 -c "
import json, sys
outputs = json.load(sys.stdin)
for key, value in outputs.items():
    print(f'{key}: {value.get(\"value\", \"\")}')
" 2>/dev/null || terraform output
fi
