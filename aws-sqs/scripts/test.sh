#!/bin/bash
# Banking Platform - Test Script
# Runs unit and integration tests

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
TEST_TYPE="all"
COVERAGE=""
VERBOSE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --coverage)
            COVERAGE="--cov=src --cov-report=html --cov-report=term"
            shift
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --unit           Run unit tests only"
            echo "  --integration    Run integration tests only"
            echo "  --coverage       Generate coverage report"
            echo "  -v, --verbose    Verbose output"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=== Banking Platform Tests ==="
echo "Test type: ${TEST_TYPE}"
echo ""

cd "${PROJECT_ROOT}"

# Create virtual environment if it doesn't exist
if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "${PROJECT_ROOT}/.venv"
fi

# Activate virtual environment
source "${PROJECT_ROOT}/.venv/bin/activate"

# Install dev dependencies
echo "Installing test dependencies..."
pip install -r requirements-dev.txt -q

# Run tests
case $TEST_TYPE in
    unit)
        echo "Running unit tests..."
        pytest tests/unit ${VERBOSE} ${COVERAGE}
        ;;
    integration)
        echo "Running integration tests..."
        pytest tests/integration ${VERBOSE} ${COVERAGE}
        ;;
    all)
        echo "Running all tests..."
        pytest tests ${VERBOSE} ${COVERAGE}
        ;;
esac

echo ""
echo "=== Tests Complete ==="
