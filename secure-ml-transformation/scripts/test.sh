#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

TEST_TYPE=${1:-all}
COVERAGE=${2:-true}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Running Tests${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Test type: ${TEST_TYPE}"
echo "Coverage: ${COVERAGE}"
echo ""

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Ensure dependencies are installed
pip install -r requirements-dev.txt -q

# Set Python path
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}Running unit tests...${NC}"
        if [ "$COVERAGE" = "true" ]; then
            pytest tests/unit -v --cov=src --cov=glue --cov-report=html --cov-report=term-missing
        else
            pytest tests/unit -v
        fi
        ;;

    integration)
        echo -e "${YELLOW}Running integration tests...${NC}"
        if [ "$COVERAGE" = "true" ]; then
            pytest tests/integration -v --cov=src --cov=glue --cov-report=html --cov-report=term-missing
        else
            pytest tests/integration -v
        fi
        ;;

    all)
        echo -e "${YELLOW}Running all tests...${NC}"
        if [ "$COVERAGE" = "true" ]; then
            pytest tests/ -v --cov=src --cov=glue --cov-report=html --cov-report=term-missing
        else
            pytest tests/ -v
        fi
        ;;

    *)
        echo -e "${RED}Unknown test type: ${TEST_TYPE}${NC}"
        echo "Usage: $0 <unit|integration|all> [coverage:true|false]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Tests complete!${NC}"
if [ "$COVERAGE" = "true" ]; then
    echo "Coverage report available at: htmlcov/index.html"
fi
