#!/bin/bash
# SMS Marketing System - Test Script
# Runs unit and integration tests

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== SMS Marketing System Tests ==="

# Create virtual environment if it doesn't exist
if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "${PROJECT_ROOT}/.venv"
fi

# Activate virtual environment
source "${PROJECT_ROOT}/.venv/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install -r "${PROJECT_ROOT}/requirements-dev.txt" -q

# Add src to PYTHONPATH
export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}"

# Run linting
echo ""
echo "Running linting..."
if command -v ruff &> /dev/null; then
    ruff check "${PROJECT_ROOT}/src" "${PROJECT_ROOT}/tests" || true
fi

# Run type checking
echo ""
echo "Running type checking..."
if command -v mypy &> /dev/null; then
    mypy "${PROJECT_ROOT}/src" --ignore-missing-imports || true
fi

# Run tests
echo ""
echo "Running tests..."
pytest "${PROJECT_ROOT}/tests" \
    -v \
    --tb=short \
    --cov="${PROJECT_ROOT}/src" \
    --cov-report=term-missing \
    --cov-report=html:"${PROJECT_ROOT}/coverage_html" \
    "${@}"

echo ""
echo "=== Tests Complete ==="
echo "Coverage report: ${PROJECT_ROOT}/coverage_html/index.html"
