#!/bin/bash
# SMS Marketing System - Destroy Script
# Destroys all infrastructure

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"

echo "=== SMS Marketing System Destruction ==="
echo ""
echo "WARNING: This will destroy all resources!"
echo ""

# Ask for confirmation
read -p "Are you sure you want to destroy all resources? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Destruction cancelled."
    exit 0
fi

# Double confirmation
read -p "Type 'destroy' to confirm: " confirm2
if [ "$confirm2" != "destroy" ]; then
    echo "Destruction cancelled."
    exit 0
fi

# Initialize Terraform
echo ""
echo "Initializing Terraform..."
cd "${TERRAFORM_DIR}"
terraform init

# Destroy resources
echo ""
echo "Destroying resources..."
terraform destroy -var-file="terraform.tfvars" -auto-approve

echo ""
echo "=== Destruction Complete ==="
