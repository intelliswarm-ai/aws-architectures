#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-eu-central-2}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Deploying SAM application..."
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"

cd "${PROJECT_ROOT}/sam"

sam build
sam deploy --config-env "${ENVIRONMENT}" --region "${REGION}"
