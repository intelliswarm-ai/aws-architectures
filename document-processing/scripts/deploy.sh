#!/bin/bash
set -e

# =============================================================================
# Deploy Script for AWS ML Platform
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Parse arguments
SKIP_BUILD=false
AUTO_APPROVE=false
DESTROY=false
PLAN_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
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
            echo "Usage: deploy.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-build    Skip building Lambda package"
            echo "  --auto-approve  Auto-approve Terraform apply"
            echo "  --destroy       Destroy all resources"
            echo "  --plan          Only run terraform plan"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}=== AWS ML Platform Deployment ===${NC}"
echo ""

# Step 1: Build (unless skipped or destroying)
if [[ "$SKIP_BUILD" == "false" && "$DESTROY" == "false" ]]; then
    echo -e "${YELLOW}Step 1: Building Lambda package...${NC}"
    "$SCRIPT_DIR/build.sh"
    echo ""
fi

# Step 2: Check Terraform
echo -e "${YELLOW}Step 2: Checking Terraform...${NC}"
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}ERROR: Terraform is not installed${NC}"
    exit 1
fi

TERRAFORM_VERSION=$(terraform --version | head -n 1)
echo "  $TERRAFORM_VERSION"
echo ""

# Step 3: Initialize Terraform
echo -e "${YELLOW}Step 3: Initializing Terraform...${NC}"
cd "$TERRAFORM_DIR"
terraform init -upgrade
echo ""

# Step 4: Validate Terraform
echo -e "${YELLOW}Step 4: Validating Terraform...${NC}"
terraform validate
echo ""

# Step 5: Plan
echo -e "${YELLOW}Step 5: Creating execution plan...${NC}"
if [[ "$DESTROY" == "true" ]]; then
    terraform plan -destroy -out=tfplan
else
    terraform plan -out=tfplan
fi
echo ""

# Exit if plan only
if [[ "$PLAN_ONLY" == "true" ]]; then
    echo -e "${GREEN}Plan complete. Run without --plan to apply.${NC}"
    rm -f tfplan
    exit 0
fi

# Step 6: Apply
echo -e "${YELLOW}Step 6: Applying changes...${NC}"
if [[ "$AUTO_APPROVE" == "true" ]]; then
    terraform apply tfplan
else
    echo ""
    read -p "Do you want to apply these changes? (yes/no): " answer
    if [[ "$answer" == "yes" ]]; then
        terraform apply tfplan
    else
        echo -e "${YELLOW}Aborted.${NC}"
        rm -f tfplan
        exit 0
    fi
fi

rm -f tfplan

# Step 7: Show outputs
if [[ "$DESTROY" == "false" ]]; then
    echo ""
    echo -e "${GREEN}=== Deployment Complete ===${NC}"
    echo ""
    echo -e "${YELLOW}Outputs:${NC}"
    terraform output
fi

echo ""
echo -e "${GREEN}Done!${NC}"
