#!/bin/bash
set -e

# ML Canary Deployment - Build Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$PROJECT_ROOT/build"
SRC_DIR="$PROJECT_ROOT/src"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}ML Canary Deployment - Building Lambda Package${NC}"

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf "$DIST_DIR" "$BUILD_DIR"
mkdir -p "$DIST_DIR" "$BUILD_DIR"

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install \
    --target "$BUILD_DIR" \
    --platform manylinux2014_x86_64 \
    --python-version 3.12 \
    --only-binary=:all: \
    -r "$PROJECT_ROOT/requirements.txt" \
    --quiet

# Copy source code
echo -e "${YELLOW}Copying source code...${NC}"
cp -r "$SRC_DIR" "$BUILD_DIR/"

# Optimize package
echo -e "${YELLOW}Optimizing package...${NC}"
find "$BUILD_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$BUILD_DIR" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

# Create ZIP
echo -e "${YELLOW}Creating deployment package...${NC}"
cd "$BUILD_DIR"
zip -r -q "$DIST_DIR/lambda.zip" .

# Show package size
PACKAGE_SIZE=$(du -h "$DIST_DIR/lambda.zip" | cut -f1)
echo -e "${GREEN}Build complete!${NC}"
echo "Package: $DIST_DIR/lambda.zip"
echo "Size: $PACKAGE_SIZE"
