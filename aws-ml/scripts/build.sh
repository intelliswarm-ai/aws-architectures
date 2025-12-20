#!/bin/bash
set -e

# =============================================================================
# Build Script for AWS ML Platform Lambda Functions
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"
SRC_DIR="$PROJECT_ROOT/src"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Building AWS ML Platform Lambda Package ===${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "  Python version: $PYTHON_VERSION"

if ! command -v pip &> /dev/null; then
    echo -e "${RED}ERROR: pip is not installed${NC}"
    exit 1
fi

# Clean previous build
echo ""
echo -e "${YELLOW}Cleaning previous build...${NC}"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# Create temporary build directory
BUILD_DIR=$(mktemp -d)
trap "rm -rf $BUILD_DIR" EXIT

echo "  Build directory: $BUILD_DIR"

# Install dependencies
echo ""
echo -e "${YELLOW}Installing dependencies...${NC}"

pip install \
    --target "$BUILD_DIR" \
    --platform manylinux2014_x86_64 \
    --python-version 3.12 \
    --only-binary=:all: \
    --upgrade \
    -r "$PROJECT_ROOT/requirements.txt" \
    2>&1 | grep -v "already satisfied" || true

# Copy source code
echo ""
echo -e "${YELLOW}Copying source code...${NC}"
cp -r "$SRC_DIR" "$BUILD_DIR/"

# Remove unnecessary files to reduce package size
echo ""
echo -e "${YELLOW}Optimizing package size...${NC}"
find "$BUILD_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$BUILD_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true

# Create ZIP package
echo ""
echo -e "${YELLOW}Creating deployment package...${NC}"

cd "$BUILD_DIR"
zip -r -q "$DIST_DIR/lambda.zip" . -x "*.git*" -x "*__pycache__*"

# Show package info
PACKAGE_SIZE=$(du -h "$DIST_DIR/lambda.zip" | cut -f1)
echo ""
echo -e "${GREEN}=== Build Complete ===${NC}"
echo "  Package: $DIST_DIR/lambda.zip"
echo "  Size: $PACKAGE_SIZE"

# Warn if package is too large
PACKAGE_BYTES=$(stat -f%z "$DIST_DIR/lambda.zip" 2>/dev/null || stat --printf="%s" "$DIST_DIR/lambda.zip" 2>/dev/null)
if [ "$PACKAGE_BYTES" -gt 262144000 ]; then
    echo -e "${YELLOW}WARNING: Package exceeds 250MB unzipped limit. Consider using Lambda layers.${NC}"
fi

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. cd terraform"
echo "  2. terraform init"
echo "  3. terraform plan"
echo "  4. terraform apply"
