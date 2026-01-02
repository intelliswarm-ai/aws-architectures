#!/bin/bash
# Banking Platform - Destroy Script
# Destroys all infrastructure

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Banking Platform Destroy ==="
echo ""
echo "WARNING: This will destroy all infrastructure!"
echo ""

"${SCRIPT_DIR}/deploy.sh" --destroy "$@"
