#!/bin/bash
set -e

# ML Canary Deployment - Terraform Deployment Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default values
SKIP_BUILD=false
AUTO_APPROVE=false
PLAN_ONLY=false

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-build      Skip building Lambda package"
    echo "  --auto-approve    Auto-approve Terraform apply"
    echo "  --plan            Only run Terraform plan"
    echo "  -h, --help        Show this help message"
}

# Parse arguments
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
        --plan)
            PLAN_ONLY=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

echo -e "${GREEN}ML Canary Deployment - Terraform Deployment${NC}"

# Build Lambda package
if [[ "$SKIP_BUILD" == "false" ]]; then
    echo -e "${YELLOW}Building Lambda package...${NC}"
    "$SCRIPT_DIR/build.sh"
fi

# Initialize Terraform
echo -e "${YELLOW}Initializing Terraform...${NC}"
cd "$TERRAFORM_DIR"
terraform init

# Run Terraform plan
echo -e "${YELLOW}Running Terraform plan...${NC}"
terraform plan -out=tfplan

if [[ "$PLAN_ONLY" == "true" ]]; then
    echo -e "${GREEN}Plan complete. Review the plan above.${NC}"
    exit 0
fi

# Apply Terraform
echo -e "${YELLOW}Applying Terraform...${NC}"
if [[ "$AUTO_APPROVE" == "true" ]]; then
    terraform apply tfplan
else
    terraform apply tfplan
fi

# Clean up plan file
rm -f tfplan

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Outputs:"
terraform output
