#!/bin/bash
# Build and install Voice Notepad V3 in one step
set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "=== Building and Installing Voice Notepad V3 ==="
echo ""

./build.sh --deb --fast
./build.sh --install
