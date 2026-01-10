#!/bin/bash
# =============================================================================
# Test Script - GenAI Knowledge Assistant
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
COVERAGE=true
LINT=true
TYPECHECK=true
UNIT_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --no-lint)
            LINT=false
            shift
            ;;
        --no-typecheck)
            TYPECHECK=false
            shift
            ;;
        --unit)
            UNIT_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --no-coverage    Skip coverage reporting"
            echo "  --no-lint        Skip linting"
            echo "  --no-typecheck   Skip type checking"
            echo "  --unit           Run unit tests only"
            echo "  -h, --help       Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

cd "$PROJECT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Running Tests - GenAI Knowledge Assistant${NC}"
echo -e "${GREEN}========================================${NC}"

# Install dev dependencies
echo -e "\n${YELLOW}Installing dev dependencies...${NC}"
pip install -r requirements-dev.txt -q

# Linting
if [ "$LINT" = true ]; then
    echo -e "\n${YELLOW}Running linter (ruff)...${NC}"
    ruff check src/ tests/ --fix || true
    ruff format src/ tests/ --check || true
fi

# Type checking
if [ "$TYPECHECK" = true ]; then
    echo -e "\n${YELLOW}Running type checker (mypy)...${NC}"
    mypy src/ --ignore-missing-imports || true
fi

# Run tests
echo -e "\n${YELLOW}Running tests...${NC}"

PYTEST_ARGS="-v"

if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=src --cov-report=term-missing --cov-report=html"
fi

if [ "$UNIT_ONLY" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS tests/unit/"
else
    PYTEST_ARGS="$PYTEST_ARGS tests/"
fi

pytest $PYTEST_ARGS

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Tests Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

if [ "$COVERAGE" = true ]; then
    echo -e "Coverage report: file://$PROJECT_DIR/htmlcov/index.html"
fi
