#!/bin/bash
# ============================================
# Test Script for Inventory Management System
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
APP_DIR="$PROJECT_ROOT/application"

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --unit          Run unit tests only"
    echo "  --integration   Run integration tests only"
    echo "  --all           Run all tests (default)"
    echo "  --coverage      Generate coverage report"
    echo "  -h, --help      Show this help message"
}

TEST_TYPE="all"
COVERAGE=false

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
        --all)
            TEST_TYPE="all"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

cd "$APP_DIR"

echo "=========================================="
echo "Running Tests"
echo "Test Type: $TEST_TYPE"
echo "Coverage: $COVERAGE"
echo "=========================================="

MVN_ARGS=""

if [[ "$COVERAGE" == "true" ]]; then
    MVN_ARGS="$MVN_ARGS jacoco:prepare-agent"
fi

case $TEST_TYPE in
    unit)
        echo "Running unit tests..."
        ./mvnw test $MVN_ARGS -Dgroups="unit"
        ;;
    integration)
        echo "Running integration tests..."
        ./mvnw test $MVN_ARGS -Dgroups="integration"
        ;;
    all)
        echo "Running all tests..."
        ./mvnw test $MVN_ARGS
        ;;
esac

if [[ "$COVERAGE" == "true" ]]; then
    echo "Generating coverage report..."
    ./mvnw jacoco:report
    echo "Coverage report: $APP_DIR/target/site/jacoco/index.html"
fi

echo "=========================================="
echo "Tests complete!"
echo "=========================================="
