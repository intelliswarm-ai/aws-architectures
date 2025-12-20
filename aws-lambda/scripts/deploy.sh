#!/bin/bash
set -e

# Task Automation System - Deploy Script
# Builds Lambda JARs and deploys infrastructure using Terraform

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="$PROJECT_ROOT/lambda"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "Task Automation System - Deployment"
echo "=============================================="
echo ""

# Parse arguments
SKIP_BUILD=false
AUTO_APPROVE=false
DESTROY=false

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
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-build] [--auto-approve] [--destroy]"
            exit 1
            ;;
    esac
done

# Step 1: Build Lambda JARs
if [[ "$SKIP_BUILD" == "false" && "$DESTROY" == "false" ]]; then
    echo -e "${YELLOW}Step 1: Building Lambda JARs...${NC}"
    "$SCRIPT_DIR/build.sh"
    echo ""
else
    echo -e "${YELLOW}Step 1: Skipping build...${NC}"
fi

# Step 2: Check Terraform
echo -e "${YELLOW}Step 2: Checking Terraform...${NC}"
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}ERROR: Terraform is not installed${NC}"
    exit 1
fi

TERRAFORM_VERSION=$(terraform version | head -n 1)
echo "Using $TERRAFORM_VERSION"
echo ""

# Step 3: Initialize Terraform
echo -e "${YELLOW}Step 3: Initializing Terraform...${NC}"
cd "$TERRAFORM_DIR"
terraform init -upgrade
echo ""

# Step 4: Validate Terraform
echo -e "${YELLOW}Step 4: Validating Terraform configuration...${NC}"
terraform validate
echo ""

# Step 5: Plan or Destroy
if [[ "$DESTROY" == "true" ]]; then
    echo -e "${YELLOW}Step 5: Planning destruction...${NC}"
    terraform plan -destroy -out=tfplan
else
    echo -e "${YELLOW}Step 5: Planning deployment...${NC}"
    terraform plan -out=tfplan
fi
echo ""

# Step 6: Apply
if [[ "$AUTO_APPROVE" == "true" ]]; then
    echo -e "${YELLOW}Step 6: Applying changes (auto-approved)...${NC}"
    terraform apply tfplan
else
    echo -e "${YELLOW}Step 6: Apply changes?${NC}"
    read -p "Do you want to apply these changes? (yes/no): " answer
    if [[ "$answer" == "yes" ]]; then
        terraform apply tfplan
    else
        echo "Deployment cancelled."
        rm -f tfplan
        exit 0
    fi
fi

# Clean up plan file
rm -f tfplan

echo ""
echo -e "${GREEN}=============================================="
if [[ "$DESTROY" == "true" ]]; then
    echo "Destruction completed successfully!"
else
    echo "Deployment completed successfully!"
fi
echo -e "==============================================${NC}"

if [[ "$DESTROY" == "false" ]]; then
    echo ""
    echo "Outputs:"
    terraform output
fi
