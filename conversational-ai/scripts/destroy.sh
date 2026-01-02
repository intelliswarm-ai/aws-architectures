#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default environment
ENVIRONMENT="${1:-dev}"

echo "Destroying aws-lex infrastructure for $ENVIRONMENT..."

"$SCRIPT_DIR/deploy.sh" -e "$ENVIRONMENT" --destroy

echo "Cleanup complete."
