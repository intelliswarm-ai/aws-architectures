#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Deploying SAM application..."
cd "$PROJECT_ROOT/sam"
sam build && sam deploy
echo "SAM deployment complete!"
