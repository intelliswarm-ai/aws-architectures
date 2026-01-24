#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Building SAM application..."

cd "${PROJECT_ROOT}/sam"

sam build --use-container

echo "Build complete!"
