#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Building Lambda Package ===${NC}"

# Create dist directory
DIST_DIR="$PROJECT_ROOT/dist"
mkdir -p "$DIST_DIR"
rm -rf "$DIST_DIR/*"

# Create temporary build directory
BUILD_DIR=$(mktemp -d)
trap "rm -rf $BUILD_DIR" EXIT

echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r "$PROJECT_ROOT/requirements.txt" -t "$BUILD_DIR" --quiet --upgrade

echo -e "${YELLOW}Copying source code...${NC}"
cp -r "$PROJECT_ROOT/src" "$BUILD_DIR/"

echo -e "${YELLOW}Creating ZIP package...${NC}"
cd "$BUILD_DIR"
zip -r "$DIST_DIR/lambda.zip" . -x "*.pyc" -x "*__pycache__*" -x "*.dist-info/*" > /dev/null

PACKAGE_SIZE=$(du -h "$DIST_DIR/lambda.zip" | cut -f1)
echo -e "${GREEN}Package created: dist/lambda.zip (${PACKAGE_SIZE})${NC}"
echo -e "${GREEN}Build complete!${NC}"
