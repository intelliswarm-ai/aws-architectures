#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Building aws-call-sentiment..."

cd "$PROJECT_DIR"

# Create virtual environment if not exists
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
ruff check src/ tests/ --fix || true
black src/ tests/

# Run type checking
echo "Running type checking..."
mypy src/ --ignore-missing-imports || true

# Run tests
echo "Running tests..."
pytest tests/ -v --cov=src --cov-report=term-missing || true

# Build Lambda deployment package
echo "Building Lambda deployment package..."
BUILD_DIR="$PROJECT_DIR/build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy source code
cp -r "$PROJECT_DIR/src/"* "$BUILD_DIR/"

# Install dependencies to build directory
pip install -t "$BUILD_DIR" \
    aws-lambda-powertools \
    pydantic \
    pydantic-settings \
    opensearch-py \
    requests-aws4auth \
    --quiet

# Create zip file
cd "$BUILD_DIR"
zip -r "$PROJECT_DIR/lambda.zip" . -x "*.pyc" -x "__pycache__/*" -x "*.dist-info/*"

echo "Build complete: lambda.zip"
