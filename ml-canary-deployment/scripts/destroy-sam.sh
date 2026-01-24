#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Destroying SAM application..."
cd "$PROJECT_ROOT/sam"
sam delete --no-prompts
echo "SAM stack destroyed!"
