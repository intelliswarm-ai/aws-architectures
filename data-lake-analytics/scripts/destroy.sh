#!/bin/bash
set -euo pipefail

# Destroy script for AWS Athena Data Lake (Terraform)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

cd "${PROJECT_DIR}/terraform"

log_warn "This will DESTROY all AWS resources managed by Terraform!"
log_warn ""
log_warn "Resources to be destroyed:"
log_warn "  - S3 buckets (raw, processed, results)"
log_warn "  - Glue database, tables, ETL job, crawler"
log_warn "  - Athena workgroup"
log_warn "  - Lambda functions"
log_warn "  - Lake Formation resources"
log_warn "  - IAM roles and policies"
log_warn "  - CloudWatch logs and alarms"
log_warn ""

read -p "Are you sure you want to destroy all resources? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log_warn "Destruction cancelled."
    exit 0
fi

# Empty S3 buckets first (required before deletion)
log_warn "Emptying S3 buckets..."

RAW_BUCKET=$(terraform output -raw raw_bucket_name 2>/dev/null || echo "")
PROCESSED_BUCKET=$(terraform output -raw processed_bucket_name 2>/dev/null || echo "")
RESULTS_BUCKET=$(terraform output -raw results_bucket_name 2>/dev/null || echo "")

for bucket in "$RAW_BUCKET" "$PROCESSED_BUCKET" "$RESULTS_BUCKET"; do
    if [ -n "$bucket" ]; then
        log_warn "  Emptying ${bucket}..."
        aws s3 rm "s3://${bucket}" --recursive 2>/dev/null || true
    fi
done

# Destroy Terraform resources
log_warn "Destroying Terraform resources..."
terraform destroy -auto-approve

log_warn ""
log_warn "All resources have been destroyed."
