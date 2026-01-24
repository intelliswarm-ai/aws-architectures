#!/bin/bash
set -e

# ML Canary Deployment - Test Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default values
COVERAGE=true
VERBOSE=false
UNIT_ONLY=false

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --no-coverage     Disable coverage reporting"
    echo "  --verbose, -v     Verbose output"
    echo "  --unit            Run only unit tests"
    echo "  -h, --help        Show this help message"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --unit)
            UNIT_ONLY=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

echo -e "${GREEN}ML Canary Deployment - Running Tests${NC}"

cd "$PROJECT_ROOT"

# Build pytest args
PYTEST_ARGS=()

if [[ "$VERBOSE" == "true" ]]; then
    PYTEST_ARGS+=("-v")
fi

if [[ "$COVERAGE" == "true" ]]; then
    PYTEST_ARGS+=("--cov=src" "--cov-report=term-missing" "--cov-report=html")
fi

if [[ "$UNIT_ONLY" == "true" ]]; then
    PYTEST_ARGS+=("tests/unit")
else
    PYTEST_ARGS+=("tests")
fi

# Run tests
echo -e "${YELLOW}Running pytest...${NC}"
python -m pytest "${PYTEST_ARGS[@]}"

# Run linting
echo ""
echo -e "${YELLOW}Running ruff...${NC}"
ruff check src tests || true

# Run type checking
echo ""
echo -e "${YELLOW}Running mypy...${NC}"
mypy src --ignore-missing-imports || true

echo ""
echo -e "${GREEN}Tests complete!${NC}"

if [[ "$COVERAGE" == "true" ]]; then
    echo "Coverage report: htmlcov/index.html"
fi
