#!/bin/bash
# Build and install Voice Notepad V3 in one step
# Combines build.sh and install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="${1:-1.1.0}"

echo "=== Voice Notepad V3 - Build & Install ==="
echo ""

# Build the package
./build.sh "$VERSION"

# Install it
./install.sh

echo "=== Done ==="
