#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default values
ENV="dev"
AUTO_APPROVE=""
DESTROY=""
SKIP_BUILD=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env|-e)
            ENV="$2"
            shift 2
            ;;
        --auto-approve|-y)
            AUTO_APPROVE="-auto-approve"
            shift
            ;;
        --destroy)
            DESTROY="true"
            shift
            ;;
        --skip-build)
            SKIP_BUILD="true"
            shift
            ;;
        -h|--help)
            echo "Usage: deploy.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --env, -e ENV      Environment (dev, staging, prod) [default: dev]"
            echo "  --auto-approve, -y  Skip approval prompt"
            echo "  --destroy          Destroy infrastructure"
            echo "  --skip-build       Skip Lambda build step"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

TFVARS_FILE="$PROJECT_ROOT/environments/${ENV}.tfvars"
if [ ! -f "$TFVARS_FILE" ]; then
    echo -e "${RED}Environment file not found: $TFVARS_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}=== Deploying to ${ENV} ===${NC}"

# Build Lambda package
if [ -z "$SKIP_BUILD" ] && [ -z "$DESTROY" ]; then
    echo -e "${YELLOW}Building Lambda package...${NC}"
    "$SCRIPT_DIR/build.sh"
fi

# Change to terraform directory
cd "$PROJECT_ROOT/terraform"

# Initialize Terraform
echo -e "${YELLOW}Initializing Terraform...${NC}"
terraform init -upgrade

# Validate
echo -e "${YELLOW}Validating configuration...${NC}"
terraform validate

if [ -n "$DESTROY" ]; then
    echo -e "${RED}=== DESTROYING INFRASTRUCTURE ===${NC}"
    terraform destroy -var-file="$TFVARS_FILE" $AUTO_APPROVE
else
    # Plan
    echo -e "${YELLOW}Planning changes...${NC}"
    terraform plan -var-file="$TFVARS_FILE" -out=tfplan

    # Apply
    echo -e "${YELLOW}Applying changes...${NC}"
    if [ -n "$AUTO_APPROVE" ]; then
        terraform apply tfplan
    else
        terraform apply -var-file="$TFVARS_FILE"
    fi

    rm -f tfplan
fi

echo -e "${GREEN}Done!${NC}"
