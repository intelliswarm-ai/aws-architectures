#!/bin/bash
# SMS Marketing System - Build Script
# Builds the Lambda deployment package

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="${PROJECT_ROOT}/dist"
SRC_DIR="${PROJECT_ROOT}/src"

echo "=== SMS Marketing System Build ==="
echo "Project root: ${PROJECT_ROOT}"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf "${DIST_DIR}"
mkdir -p "${DIST_DIR}"

# Create virtual environment if it doesn't exist
if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "${PROJECT_ROOT}/.venv"
fi

# Activate virtual environment
source "${PROJECT_ROOT}/.venv/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install -r "${PROJECT_ROOT}/requirements.txt" -q

# Run linting and type checking
echo "Running code quality checks..."
if command -v ruff &> /dev/null; then
    ruff check "${SRC_DIR}" --fix || true
fi

if command -v mypy &> /dev/null; then
    mypy "${SRC_DIR}" --ignore-missing-imports || true
fi

# Create Lambda package
echo "Creating Lambda deployment package..."
PACKAGE_DIR="${DIST_DIR}/package"
mkdir -p "${PACKAGE_DIR}"

# Copy source code
cp -r "${SRC_DIR}"/* "${PACKAGE_DIR}/"

# Install dependencies to package
pip install -r "${PROJECT_ROOT}/requirements.txt" -t "${PACKAGE_DIR}" -q

# Remove unnecessary files
find "${PACKAGE_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${PACKAGE_DIR}" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find "${PACKAGE_DIR}" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find "${PACKAGE_DIR}" -name "*.pyc" -delete 2>/dev/null || true

# Create ZIP
echo "Creating ZIP archive..."
cd "${PACKAGE_DIR}"
zip -r "${DIST_DIR}/lambda.zip" . -q
cd "${PROJECT_ROOT}"

# Calculate package size
PACKAGE_SIZE=$(du -h "${DIST_DIR}/lambda.zip" | cut -f1)
echo "Package created: ${DIST_DIR}/lambda.zip (${PACKAGE_SIZE})"

# Create layer package (optional)
if [ "${CREATE_LAYER:-false}" = "true" ]; then
    echo "Creating Lambda layer..."
    LAYER_DIR="${DIST_DIR}/layer/python"
    mkdir -p "${LAYER_DIR}"
    pip install -r "${PROJECT_ROOT}/requirements.txt" -t "${LAYER_DIR}" -q

    # Remove unnecessary files
    find "${LAYER_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "${LAYER_DIR}" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

    cd "${DIST_DIR}/layer"
    zip -r "${DIST_DIR}/layer.zip" . -q
    cd "${PROJECT_ROOT}"

    LAYER_SIZE=$(du -h "${DIST_DIR}/layer.zip" | cut -f1)
    echo "Layer created: ${DIST_DIR}/layer.zip (${LAYER_SIZE})"
fi

echo ""
echo "=== Build Complete ==="
echo "Lambda package: ${DIST_DIR}/lambda.zip"
