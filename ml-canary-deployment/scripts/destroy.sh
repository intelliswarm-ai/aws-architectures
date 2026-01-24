#!/bin/bash
set -e

# ML Canary Deployment - Terraform Destroy Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

AUTO_APPROVE=false

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --auto-approve    Auto-approve Terraform destroy"
    echo "  -h, --help        Show this help message"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-approve)
            AUTO_APPROVE=true
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

echo -e "${RED}ML Canary Deployment - Terraform Destroy${NC}"
echo ""
echo -e "${YELLOW}WARNING: This will destroy all resources!${NC}"
echo ""

cd "$TERRAFORM_DIR"

if [[ "$AUTO_APPROVE" == "true" ]]; then
    terraform destroy -auto-approve
else
    terraform destroy
fi

echo -e "${GREEN}Destroy complete!${NC}"
