#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Running Tests ===${NC}"

cd "$PROJECT_ROOT"

# Run pytest
echo -e "${YELLOW}Running pytest...${NC}"
python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

# Run ruff
echo -e "${YELLOW}Running ruff linter...${NC}"
python -m ruff check src tests || true

# Run mypy
echo -e "${YELLOW}Running mypy type checker...${NC}"
python -m mypy src --ignore-missing-imports || true

echo -e "${GREEN}Tests complete!${NC}"
