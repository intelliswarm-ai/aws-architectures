#!/bin/bash
set -e

# =============================================================================
# Test Script for AWS ML Platform
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Running Tests ===${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install -r requirements-dev.txt -q

# Run linting
echo ""
echo -e "${YELLOW}Running linting (ruff)...${NC}"
ruff check src/ tests/ || true

# Run type checking
echo ""
echo -e "${YELLOW}Running type checking (mypy)...${NC}"
mypy src/ --ignore-missing-imports || true

# Run tests
echo ""
echo -e "${YELLOW}Running tests (pytest)...${NC}"
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

echo ""
echo -e "${GREEN}=== Tests Complete ===${NC}"
echo "  Coverage report: htmlcov/index.html"
