#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-eu-central-2}

echo "Destroying SAM application..."
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"

STACK_NAME="secure-ml-transform-lambda-${ENVIRONMENT}"

sam delete \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --no-prompts
