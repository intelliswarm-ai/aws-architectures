#!/bin/bash
set -euo pipefail

# Deploy script for AWS Athena Data Lake (Terraform)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

# Configuration
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-eu-central-2}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

cd "${PROJECT_DIR}"

# Check if build artifacts exist
if [ ! -d "dist" ] || [ ! -f "dist/layer.zip" ]; then
    log_warn "Build artifacts not found. Running build first..."
    ./scripts/build.sh
fi

# Navigate to terraform directory
cd terraform

# Initialize Terraform
log_info "Initializing Terraform..."
terraform init -upgrade

# Create tfvars file if it doesn't exist
if [ ! -f "terraform.tfvars" ]; then
    log_info "Creating terraform.tfvars..."
    cat > terraform.tfvars <<EOF
environment = "${ENVIRONMENT}"
aws_region  = "${AWS_REGION}"

# Uncomment and set Lake Formation admins
# lakeformation_admin_arns = ["arn:aws:iam::ACCOUNT_ID:role/Admin"]

tags = {
  Project     = "athena-datalake"
  Environment = "${ENVIRONMENT}"
  ManagedBy   = "terraform"
}
EOF
fi

# Plan
log_info "Planning Terraform changes..."
terraform plan -out=tfplan

# Confirm deployment
echo ""
read -p "Do you want to apply these changes? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log_warn "Deployment cancelled."
    exit 0
fi

# Apply
log_info "Applying Terraform changes..."
terraform apply tfplan

# Clean up plan file
rm -f tfplan

# Output results
log_info ""
log_info "Deployment complete!"
log_info ""
log_info "Outputs:"
terraform output

log_info ""
log_info "To upload Lambda packages to S3, run:"
log_info "  aws s3 cp dist/layer.zip s3://\$(terraform output -raw results_bucket_name)/lambda/"
log_info "  aws s3 cp dist/ingest.zip s3://\$(terraform output -raw results_bucket_name)/lambda/"
log_info "  aws s3 cp dist/etl.zip s3://\$(terraform output -raw results_bucket_name)/lambda/"
log_info "  aws s3 cp dist/query.zip s3://\$(terraform output -raw results_bucket_name)/lambda/"
log_info "  aws s3 cp dist/api.zip s3://\$(terraform output -raw results_bucket_name)/lambda/"
log_info ""
log_info "To upload Glue ETL script:"
log_info "  aws s3 cp glue/etl_job.py s3://\$(terraform output -raw results_bucket_name)/glue-scripts/"
