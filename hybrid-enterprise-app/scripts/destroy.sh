#!/bin/bash
# ============================================
# Destroy Script - Remove AWS Resources
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

ENVIRONMENT="${ENVIRONMENT:-dev}"

echo "=========================================="
echo "WARNING: This will destroy all resources!"
echo "Environment: $ENVIRONMENT"
echo "=========================================="

read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [[ "$CONFIRM" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

cd "$TERRAFORM_DIR"

echo "Running terraform destroy..."
terraform destroy -auto-approve

echo "=========================================="
echo "All resources have been destroyed."
echo "=========================================="
