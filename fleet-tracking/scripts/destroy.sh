#!/bin/bash
# GPS Tracking System - Destroy Script
# Destroys all infrastructure

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"

ENVIRONMENT="${ENVIRONMENT:-dev}"
AUTO_APPROVE="${AUTO_APPROVE:-false}"

echo "=== GPS Tracking System - Destroy Infrastructure ==="
echo "Environment: ${ENVIRONMENT}"
echo ""
echo "WARNING: This will destroy all resources!"
echo ""

cd "${TERRAFORM_DIR}"

if [ "${AUTO_APPROVE}" = "true" ]; then
    terraform destroy \
        -var="environment=${ENVIRONMENT}" \
        -var-file="terraform.tfvars" \
        -auto-approve
else
    terraform destroy \
        -var="environment=${ENVIRONMENT}" \
        -var-file="terraform.tfvars"
fi

echo ""
echo "=== Infrastructure Destroyed ==="
