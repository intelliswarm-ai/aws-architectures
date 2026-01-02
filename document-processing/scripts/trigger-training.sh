#!/bin/bash
set -e

# =============================================================================
# Trigger SageMaker Training Job
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default values
REGION="${AWS_REGION:-eu-central-2}"
TRAINING_DATA=""
HYPERPARAMETERS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            REGION="$2"
            shift 2
            ;;
        --training-data)
            TRAINING_DATA="$2"
            shift 2
            ;;
        --hyperparameters)
            HYPERPARAMETERS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: trigger-training.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --region REGION         AWS region (default: us-east-1)"
            echo "  --training-data S3_URI  S3 URI for training data"
            echo "  --hyperparameters JSON  JSON string of hyperparameters"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}=== Triggering SageMaker Training ===${NC}"
echo ""

# Get Lambda function name from Terraform output
cd "$PROJECT_ROOT/terraform"
LAMBDA_NAME=$(terraform output -raw training_pipeline_function_name 2>/dev/null || echo "")

if [ -z "$LAMBDA_NAME" ]; then
    # Fall back to default name
    LAMBDA_NAME="ml-platform-dev-training-pipeline"
fi

echo -e "${YELLOW}Lambda function: $LAMBDA_NAME${NC}"
echo -e "${YELLOW}Region: $REGION${NC}"

# Build payload
PAYLOAD='{"action": "start_training"'

if [ -n "$TRAINING_DATA" ]; then
    PAYLOAD="$PAYLOAD, \"training_data_uri\": \"$TRAINING_DATA\""
fi

if [ -n "$HYPERPARAMETERS" ]; then
    PAYLOAD="$PAYLOAD, \"hyperparameters\": $HYPERPARAMETERS"
fi

PAYLOAD="$PAYLOAD}"

echo -e "${YELLOW}Payload: $PAYLOAD${NC}"
echo ""

# Invoke Lambda
echo -e "${YELLOW}Invoking training Lambda...${NC}"
aws lambda invoke \
    --function-name "$LAMBDA_NAME" \
    --region "$REGION" \
    --payload "$PAYLOAD" \
    --cli-binary-format raw-in-base64-out \
    response.json

echo ""
echo -e "${GREEN}Response:${NC}"
cat response.json | python3 -m json.tool 2>/dev/null || cat response.json
rm -f response.json

echo ""
echo -e "${GREEN}Done!${NC}"
