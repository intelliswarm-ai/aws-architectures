#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Building aws-lex-airline-chatbot..."

cd "$PROJECT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -e ".[dev]"

# Run linting
echo "Running linting..."
ruff check src/ --fix || true

# Run type checking
echo "Running type checking..."
mypy src/ || true

# Build Lambda package
echo "Building Lambda package..."
BUILD_DIR="$PROJECT_DIR/build"
PACKAGE_DIR="$BUILD_DIR/package"

rm -rf "$BUILD_DIR"
mkdir -p "$PACKAGE_DIR"

# Install production dependencies
pip install -t "$PACKAGE_DIR" \
    boto3 \
    pydantic \
    pydantic-settings \
    aws-lambda-powertools

# Copy source code
cp -r "$PROJECT_DIR/src" "$PACKAGE_DIR/"

# Create zip
cd "$PACKAGE_DIR"
zip -r "$BUILD_DIR/lambda.zip" . -x "*.pyc" -x "__pycache__/*" -x "*.dist-info/*"

# Copy to terraform modules
mkdir -p "$PROJECT_DIR/terraform/modules/lambda"
cp "$BUILD_DIR/lambda.zip" "$PROJECT_DIR/terraform/modules/lambda/dummy.zip"

echo "Build complete! Lambda package: $BUILD_DIR/lambda.zip"
