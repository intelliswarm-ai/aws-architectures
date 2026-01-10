#!/bin/bash
# =============================================================================
# Deploy Script - GenAI Knowledge Assistant (SAM)
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SAM_DIR="$PROJECT_DIR/sam"

# Default values
ENVIRONMENT="dev"
GUIDED=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --guided)
            GUIDED=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -e, --env ENV   Environment (dev, staging, prod) [default: dev]"
            echo "  --guided        Run guided deployment"
            echo "  -h, --help      Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying GenAI Knowledge Assistant (SAM)${NC}"
echo -e "${GREEN}Environment: $ENVIRONMENT${NC}"
echo -e "${GREEN}========================================${NC}"

# Check SAM CLI
if ! command -v sam &> /dev/null; then
    echo -e "${RED}Error: AWS SAM CLI is required${NC}"
    echo "Install: pip install aws-sam-cli"
    exit 1
fi

cd "$SAM_DIR"

# Build
echo -e "\n${YELLOW}Building SAM application...${NC}"
sam build

# Validate
echo -e "\n${YELLOW}Validating template...${NC}"
sam validate --lint

# Deploy
echo -e "\n${YELLOW}Deploying to AWS...${NC}"

if [ "$GUIDED" = true ]; then
    sam deploy --guided --config-env "$ENVIRONMENT"
else
    sam deploy --config-env "$ENVIRONMENT"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

# Show stack outputs
STACK_NAME="genai-assistant-${ENVIRONMENT}"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs' \
    --output table 2>/dev/null || echo "Stack outputs not available"
