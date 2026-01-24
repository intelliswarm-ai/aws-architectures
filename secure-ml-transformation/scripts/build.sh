#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Building Secure ML Transformation${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

cd "$PROJECT_ROOT"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run linting
echo -e "${YELLOW}Running linting...${NC}"
ruff check src/ glue/ || true

# Run type checking
echo -e "${YELLOW}Running type checking...${NC}"
mypy src/ --ignore-missing-imports || true

# Run formatting check
echo -e "${YELLOW}Checking code formatting...${NC}"
black --check src/ glue/ || true

echo ""
echo -e "${GREEN}Build complete!${NC}"
