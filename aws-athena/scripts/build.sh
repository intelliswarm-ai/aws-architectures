#!/bin/bash
set -euo pipefail

# Build script for AWS Athena Data Lake

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

cd "${PROJECT_DIR}"

# Clean dist directory
log_info "Cleaning dist directory..."
rm -rf dist
mkdir -p dist

# Install dependencies
log_info "Installing dependencies..."
pip install -r requirements.txt --quiet

# Create Lambda layer
log_info "Creating Lambda layer..."
mkdir -p dist/python
pip install -r requirements.txt -t dist/python/ --quiet
cd dist
zip -rq layer.zip python/
rm -rf python/
cd ..

# Package Lambda functions
log_info "Packaging Lambda functions..."

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

# Copy source code
cp -r src "${TEMP_DIR}/"
cp -r glue "${TEMP_DIR}/" 2>/dev/null || true

# Package each handler
for handler in ingest etl query api; do
    log_info "  - Packaging ${handler} handler..."
    cd "${TEMP_DIR}"
    zip -rq "${PROJECT_DIR}/dist/${handler}.zip" src/
    cd "${PROJECT_DIR}"
done

# Package Glue ETL script
if [ -d "glue" ]; then
    log_info "Packaging Glue ETL script..."
    cd glue
    zip -q "${PROJECT_DIR}/dist/glue_etl.zip" etl_job.py
    cd ..
fi

log_info ""
log_info "Build complete! Artifacts in dist/:"
ls -lh dist/

log_info ""
log_info "Next steps:"
log_info "  1. Run ./scripts/deploy.sh to deploy with Terraform"
log_info "  2. Or run ./cloudformation/deploy-cfn.sh for CloudFormation"
