#!/bin/bash
# Banking Platform - Build Script
# Builds Lambda and EC2 application deployment packages

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="${PROJECT_ROOT}/dist"
SRC_DIR="${PROJECT_ROOT}/src"

echo "=== Banking Platform Build ==="
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
    echo "  - Running ruff..."
    ruff check "${SRC_DIR}" --fix || true
fi

if command -v mypy &> /dev/null; then
    echo "  - Running mypy..."
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

# Create Lambda ZIP
echo "Creating Lambda ZIP archive..."
cd "${PACKAGE_DIR}"
zip -r "${DIST_DIR}/lambda.zip" . -q
cd "${PROJECT_ROOT}"

# Calculate Lambda package size
LAMBDA_SIZE=$(du -h "${DIST_DIR}/lambda.zip" | cut -f1)
echo "Lambda package created: ${DIST_DIR}/lambda.zip (${LAMBDA_SIZE})"

# Create EC2 application package
echo "Creating EC2 application package..."
APP_DIR="${DIST_DIR}/app"
mkdir -p "${APP_DIR}"

# Copy source code and requirements
cp -r "${SRC_DIR}" "${APP_DIR}/"
cp "${PROJECT_ROOT}/requirements.txt" "${APP_DIR}/"
cp "${PROJECT_ROOT}/pyproject.toml" "${APP_DIR}/"

# Create app ZIP
cd "${APP_DIR}"
zip -r "${DIST_DIR}/app.zip" . -q
cd "${PROJECT_ROOT}"

# Calculate EC2 app package size
APP_SIZE=$(du -h "${DIST_DIR}/app.zip" | cut -f1)
echo "EC2 app package created: ${DIST_DIR}/app.zip (${APP_SIZE})"

echo ""
echo "=== Build Complete ==="
echo "Lambda package: ${DIST_DIR}/lambda.zip (${LAMBDA_SIZE})"
echo "EC2 app package: ${DIST_DIR}/app.zip (${APP_SIZE})"
