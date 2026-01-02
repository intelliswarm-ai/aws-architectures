#!/bin/bash
set -e

# Task Automation System - Build Script
# Builds all Lambda JAR files using Maven

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="$PROJECT_ROOT/lambda"

echo "=============================================="
echo "Building Task Automation System Lambda JARs"
echo "=============================================="
echo ""

cd "$LAMBDA_DIR"

# Check if Maven is installed
if ! command -v mvn &> /dev/null; then
    echo "ERROR: Maven is not installed or not in PATH"
    echo "Please install Maven: https://maven.apache.org/install.html"
    exit 1
fi

# Check Java version
JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
if [[ "$JAVA_VERSION" -lt 21 ]]; then
    echo "WARNING: Java 21 is recommended. Current version: $JAVA_VERSION"
fi

echo "Building all modules..."
echo ""

# Clean and build
mvn clean package -DskipTests

echo ""
echo "=============================================="
echo "Build completed successfully!"
echo "=============================================="
echo ""
echo "Generated JARs:"
find . -name "*.jar" -path "*/target/*" -not -name "*-sources.jar" -not -name "*-javadoc.jar" | while read jar; do
    size=$(du -h "$jar" | cut -f1)
    echo "  $jar ($size)"
done

echo ""
echo "Next steps:"
echo "  1. cd ../terraform"
echo "  2. terraform init"
echo "  3. terraform plan"
echo "  4. terraform apply"
