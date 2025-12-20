#!/bin/bash
set -e

# Task Automation System - Test Script
# Runs all unit tests

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="$PROJECT_ROOT/lambda"

echo "=============================================="
echo "Running Task Automation System Tests"
echo "=============================================="
echo ""

cd "$LAMBDA_DIR"

# Check if Maven is installed
if ! command -v mvn &> /dev/null; then
    echo "ERROR: Maven is not installed or not in PATH"
    exit 1
fi

# Run tests
echo "Running unit tests..."
mvn test

echo ""
echo "=============================================="
echo "All tests passed!"
echo "=============================================="
