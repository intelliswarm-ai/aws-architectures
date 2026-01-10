#!/bin/bash
# =============================================================================
# Build Script - GenAI Knowledge Assistant
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/dist"
LAMBDA_ZIP="$BUILD_DIR/lambda.zip"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Building GenAI Knowledge Assistant${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PYTHON_VERSION"

if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip is required${NC}"
    exit 1
fi

# Clean previous build
echo -e "\n${YELLOW}Cleaning previous build...${NC}"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create temporary build directory
TEMP_BUILD=$(mktemp -d)
trap "rm -rf $TEMP_BUILD" EXIT

echo -e "\n${YELLOW}Installing dependencies...${NC}"

# Install production dependencies
pip install \
    --target "$TEMP_BUILD" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    --upgrade \
    -r "$PROJECT_DIR/requirements.txt" 2>/dev/null || \
pip install \
    --target "$TEMP_BUILD" \
    --upgrade \
    -r "$PROJECT_DIR/requirements.txt"

# Copy source code
echo -e "\n${YELLOW}Copying source code...${NC}"
cp -r "$PROJECT_DIR/src" "$TEMP_BUILD/"

# Remove unnecessary files
echo -e "\n${YELLOW}Optimizing package...${NC}"
find "$TEMP_BUILD" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_BUILD" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$TEMP_BUILD" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_BUILD" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_BUILD" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_BUILD" -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

# Create ZIP
echo -e "\n${YELLOW}Creating Lambda package...${NC}"
cd "$TEMP_BUILD"
zip -r "$LAMBDA_ZIP" . -x "*.git*" -x "*__pycache__*" -x "*.pyc" > /dev/null

# Check package size
PACKAGE_SIZE=$(du -h "$LAMBDA_ZIP" | cut -f1)
PACKAGE_SIZE_BYTES=$(stat -f%z "$LAMBDA_ZIP" 2>/dev/null || stat -c%s "$LAMBDA_ZIP" 2>/dev/null)

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Package: $LAMBDA_ZIP"
echo -e "Size: $PACKAGE_SIZE"

# Warn if package is large
if [ "$PACKAGE_SIZE_BYTES" -gt 262144000 ]; then  # 250MB
    echo -e "${RED}Warning: Package exceeds 250MB limit!${NC}"
    exit 1
elif [ "$PACKAGE_SIZE_BYTES" -gt 52428800 ]; then  # 50MB
    echo -e "${YELLOW}Note: Package exceeds 50MB, will require S3 upload${NC}"
fi

echo -e "\n${GREEN}Next steps:${NC}"
echo "  1. Deploy with Terraform: cd terraform && terraform apply"
echo "  2. Deploy with SAM: cd sam && sam deploy"
echo "  3. Run tests: ./scripts/test.sh"
