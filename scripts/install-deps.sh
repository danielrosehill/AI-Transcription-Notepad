#!/bin/bash
# Install system dependencies for Voice Notepad on Linux
# Run with: ./scripts/install-deps.sh

set -e

echo "=================================="
echo "Voice Notepad - Dependency Check"
echo "=================================="
echo

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "This script is for Linux only."
    echo "On macOS: brew install ffmpeg"
    echo "On Windows: download FFmpeg from https://ffmpeg.org/download.html"
    exit 1
fi

# Track what needs installing
NEEDS_INSTALL=()

# Check FFmpeg
echo -n "Checking FFmpeg... "
if command -v ffmpeg &> /dev/null; then
    echo "✓ installed ($(ffmpeg -version 2>&1 | head -n1 | cut -d' ' -f3))"
else
    echo "✗ not found"
    NEEDS_INSTALL+=("ffmpeg")
fi

# Check libc++1 (required for TEN VAD)
echo -n "Checking libc++1... "
if ldconfig -p 2>/dev/null | grep -q "libc++.so.1"; then
    echo "✓ installed"
else
    echo "✗ not found (required for VAD)"
    NEEDS_INSTALL+=("libc++1")
fi

# Check uv (Python package manager)
echo -n "Checking uv... "
if command -v uv &> /dev/null; then
    echo "✓ installed ($(uv --version 2>&1 | cut -d' ' -f2))"
else
    echo "✗ not found (recommended)"
    echo "  Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

echo

# Install missing dependencies
if [ ${#NEEDS_INSTALL[@]} -eq 0 ]; then
    echo "✓ All dependencies are installed!"
    exit 0
fi

echo "Missing dependencies: ${NEEDS_INSTALL[*]}"
echo

# Detect package manager
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt-get"
    PKG_INSTALL="apt-get install -y"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    PKG_INSTALL="dnf install -y"
    # Fedora uses different package names
    NEEDS_INSTALL=("${NEEDS_INSTALL[@]/libc++1/libcxx}")
elif command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
    PKG_INSTALL="pacman -S --noconfirm"
    # Arch uses different package names
    NEEDS_INSTALL=("${NEEDS_INSTALL[@]/libc++1/libc++}")
else
    echo "Could not detect package manager (apt, dnf, or pacman)."
    echo "Please install manually: ${NEEDS_INSTALL[*]}"
    exit 1
fi

echo "Installing with $PKG_MANAGER..."
echo "This requires sudo access."
echo

# Build install command
PACKAGES="${NEEDS_INSTALL[*]}"
sudo $PKG_INSTALL $PACKAGES

echo
echo "✓ Dependencies installed successfully!"
