#!/bin/bash
# ============================================
# Build Script for Inventory Management System
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
APP_DIR="$PROJECT_ROOT/application"

echo "=========================================="
echo "Building Inventory Management Application"
echo "=========================================="

cd "$APP_DIR"

# Clean previous builds
echo "Cleaning previous builds..."
./mvnw clean

# Run tests
if [[ "$SKIP_TESTS" != "true" ]]; then
    echo "Running tests..."
    ./mvnw test
else
    echo "Skipping tests..."
fi

# Build the application
echo "Building application..."
./mvnw package -DskipTests

# Create deployment package
echo "Creating deployment package..."
ARTIFACT_NAME="inventory-management"
VERSION=$(./mvnw help:evaluate -Dexpression=project.version -q -DforceStdout)
JAR_FILE="target/${ARTIFACT_NAME}-${VERSION}.jar"

if [[ ! -f "$JAR_FILE" ]]; then
    echo "ERROR: JAR file not found: $JAR_FILE"
    exit 1
fi

# Create EB deployment bundle
DEPLOY_DIR="$PROJECT_ROOT/deploy"
mkdir -p "$DEPLOY_DIR"

# Create Procfile for Elastic Beanstalk
cat > "$DEPLOY_DIR/Procfile" << EOF
web: java -jar ${ARTIFACT_NAME}-${VERSION}.jar --server.port=5000
EOF

# Copy JAR and .ebextensions
cp "$JAR_FILE" "$DEPLOY_DIR/"
cp -r "$APP_DIR/.ebextensions" "$DEPLOY_DIR/" 2>/dev/null || true

# Create ZIP bundle
cd "$DEPLOY_DIR"
BUNDLE_NAME="${ARTIFACT_NAME}-${VERSION}-$(date +%Y%m%d%H%M%S).zip"
zip -r "$BUNDLE_NAME" .

echo "=========================================="
echo "Build complete!"
echo "Deployment bundle: $DEPLOY_DIR/$BUNDLE_NAME"
echo "=========================================="
