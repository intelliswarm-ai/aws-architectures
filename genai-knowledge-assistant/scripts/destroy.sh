#!/bin/bash
# =============================================================================
# Destroy Script - GenAI Knowledge Assistant
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${RED}========================================${NC}"
echo -e "${RED}WARNING: This will destroy all resources${NC}"
echo -e "${RED}========================================${NC}"

read -p "Are you sure you want to destroy? Type 'destroy' to confirm: " CONFIRM

if [ "$CONFIRM" != "destroy" ]; then
    echo -e "${YELLOW}Cancelled.${NC}"
    exit 0
fi

"$SCRIPT_DIR/deploy.sh" --destroy --auto-approve "$@"
