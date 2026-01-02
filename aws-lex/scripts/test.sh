#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run tests
echo "Running unit tests..."
pytest tests/unit -v --cov=src --cov-report=term-missing --cov-report=html

# Run integration tests if requested
if [ "$1" == "--integration" ]; then
    echo "Running integration tests..."
    pytest tests/integration -v
fi

echo "Tests complete!"
