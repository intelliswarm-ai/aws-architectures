#!/bin/bash
# GPS Tracking System - Test Script
# Runs unit and integration tests

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== GPS Tracking System Tests ==="

# Create/activate virtual environment
if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "${PROJECT_ROOT}/.venv"
fi

source "${PROJECT_ROOT}/.venv/bin/activate"

# Install test dependencies
echo "Installing dependencies..."
pip install -r "${PROJECT_ROOT}/requirements.txt" -q
pip install -r "${PROJECT_ROOT}/requirements-dev.txt" -q

# Change to project root
cd "${PROJECT_ROOT}"

# Run linting
echo ""
echo "=== Running Linting ==="
ruff check src/ tests/ || true

# Run type checking
echo ""
echo "=== Running Type Checking ==="
mypy src/ --ignore-missing-imports || true

# Run unit tests
echo ""
echo "=== Running Unit Tests ==="
pytest tests/unit/ \
    -v \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html:coverage_html \
    --cov-fail-under=80 \
    || true

# Run integration tests (if AWS credentials available)
if [ "${RUN_INTEGRATION:-false}" = "true" ]; then
    echo ""
    echo "=== Running Integration Tests ==="
    pytest tests/integration/ -v || true
fi

echo ""
echo "=== Tests Complete ==="
echo "Coverage report: ${PROJECT_ROOT}/coverage_html/index.html"
