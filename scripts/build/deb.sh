#!/bin/bash
# Build a Debian package for Voice Notepad V3
# Output: dist/voice-notepad_VERSION_amd64.deb
#
# Uses venv caching for fast rebuilds - only reinstalls deps when requirements.txt changes
#
# Usage: ./scripts/build/deb.sh [VERSION] [--fast] [--local]
#   --fast: Skip compression for faster builds (larger .deb, good for dev iteration)
#   --local: Version becomes VERSION~local<timestamp>. For builds installed on this machine
#            (dev builds, release.sh). "~" sorts below the bare version, so the CI-built
#            release of VERSION replaces it through apt instead of clashing with it. Without
#            it, a local and a CI build both claimed 1.14.25 and apt listed the package as
#            "upgradable from 1.14.25 to 1.14.25" (2026-10-20).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
cd "$PROJECT_ROOT"

# Parse arguments
FAST_MODE=false
LOCAL_BUILD=false
VERSION_ARG=""

for arg in "$@"; do
    case $arg in
        --fast)
            FAST_MODE=true
            ;;
        --local)
            LOCAL_BUILD=true
            ;;
        *)
            VERSION_ARG="$arg"
            ;;
    esac
done

# Get version: use argument if provided, otherwise read from pyproject.toml
if [ -n "$VERSION_ARG" ]; then
    VERSION="$VERSION_ARG"
elif [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
    VERSION=$(grep -Po '(?<=^version = ")[^"]+' "$PROJECT_ROOT/pyproject.toml")
    if [ -z "$VERSION" ]; then
        echo "Error: Could not extract version from pyproject.toml"
        exit 1
    fi
else
    echo "Error: No version specified and pyproject.toml not found"
    exit 1
fi

if [ "$LOCAL_BUILD" = true ]; then
    VERSION="${VERSION}~local$(date +%Y%m%d%H%M%S)"
fi

# The bundled venv only runs on the Python minor it was built with, so pin it.
# The old "python3 (>= 3.10)" let a 3.10 build (CI on Ubuntu 22.04) install on 3.14,
# where it cannot import its own packages.
PY_MM=$(/usr/bin/python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
PY_NEXT=$(/usr/bin/python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1] + 1}")')

PACKAGE_NAME="voice-notepad"
ARCH="amd64"

# Cache directory for venv
CACHE_DIR="$PROJECT_ROOT/.build-cache"
CACHED_VENV="$CACHE_DIR/venv"
REQUIREMENTS_HASH_FILE="$CACHE_DIR/requirements.hash"

if [ "$FAST_MODE" = true ]; then
    echo "=== Building Voice Notepad V3 - v${VERSION} (FAST MODE) ==="
else
    echo "=== Building Voice Notepad V3 - v${VERSION} ==="
fi
echo ""

# Build directory
BUILD_DIR="$PROJECT_ROOT/build/deb"
INSTALL_DIR="$BUILD_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}"

# Clean previous build (but keep cache!)
rm -rf "$BUILD_DIR"
mkdir -p "$INSTALL_DIR"
mkdir -p "$CACHE_DIR"

# Create directory structure
mkdir -p "$INSTALL_DIR/DEBIAN"
mkdir -p "$INSTALL_DIR/opt/voice-notepad"
mkdir -p "$INSTALL_DIR/usr/bin"
mkdir -p "$INSTALL_DIR/usr/share/applications"
mkdir -p "$INSTALL_DIR/usr/share/icons/hicolor/128x128/apps"

# Check if we need to rebuild the venv
# Key includes the Python version: a venv only works with the interpreter it was built
# against, and a requirements-only key reused a 3.13 venv after the move to 3.14.
CURRENT_HASH=$( { cat app/requirements.txt; /usr/bin/python3 -V; } | sha256sum | cut -d' ' -f1)
CACHED_HASH=""
if [ -f "$REQUIREMENTS_HASH_FILE" ]; then
    CACHED_HASH=$(cat "$REQUIREMENTS_HASH_FILE")
fi

if [ "$CURRENT_HASH" = "$CACHED_HASH" ] && [ -d "$CACHED_VENV" ]; then
    echo "Using cached venv (requirements unchanged)..."
    # Use hardlinks for near-instant copy (same filesystem)
    cp -al "$CACHED_VENV" "$INSTALL_DIR/opt/voice-notepad/.venv"
else
    echo "Creating virtual environment and installing dependencies..."

    # Create venv using uv with system Python (not uv-managed)
    uv venv "$INSTALL_DIR/opt/voice-notepad/.venv" --python /usr/bin/python3 --seed
    source "$INSTALL_DIR/opt/voice-notepad/.venv/bin/activate"

    # Install dependencies using uv
    uv pip install -r app/requirements.txt

    deactivate 2>/dev/null || true

    # Cache the venv for next time
    echo "Caching venv for future builds..."
    rm -rf "$CACHED_VENV"
    cp -a "$INSTALL_DIR/opt/voice-notepad/.venv" "$CACHED_VENV"
    echo "$CURRENT_HASH" > "$REQUIREMENTS_HASH_FILE"
fi

# Copy source files
echo "Copying application files..."
cp -r app/src "$INSTALL_DIR/opt/voice-notepad/"
cp -r app/assets "$INSTALL_DIR/opt/voice-notepad/"
cp app/requirements.txt "$INSTALL_DIR/opt/voice-notepad/"

# Fix permissions for all installed files
chmod -R a+rX "$INSTALL_DIR/opt/voice-notepad"

# Create launcher script (uses venv python directly for KDE/Wayland compatibility)
cat > "$INSTALL_DIR/opt/voice-notepad/voice-notepad" << 'EOF'
#!/bin/bash
cd /opt/voice-notepad
export PATH="/usr/bin:$PATH"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-wayland}"

SITE_PACKAGES=$(find .venv/lib -name "site-packages" -type d | head -1)
export PYTHONPATH="$SITE_PACKAGES:$PYTHONPATH"

exec .venv/bin/python -m src.main "$@"
EOF
chmod +x "$INSTALL_DIR/opt/voice-notepad/voice-notepad"

# Create symlink in /usr/bin
ln -s /opt/voice-notepad/voice-notepad "$INSTALL_DIR/usr/bin/voice-notepad"

# Create desktop entry
cat > "$INSTALL_DIR/usr/share/applications/voice-notepad.desktop" << EOF
[Desktop Entry]
Name=Voice Notepad
Comment=Voice recording with AI-powered transcription
Exec=/opt/voice-notepad/voice-notepad
Icon=voice-notepad
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Utility;
Keywords=voice;transcription;ai;speech;recording;
StartupWMClass=voice-notepad
EOF

# Copy app icon
cp "$PROJECT_ROOT/app/assets/icon.svg" "$INSTALL_DIR/usr/share/icons/hicolor/128x128/apps/voice-notepad.svg"

# Calculate installed size (in KB)
INSTALLED_SIZE=$(du -sk "$INSTALL_DIR/opt" | cut -f1)

# Create control file
cat > "$INSTALL_DIR/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: sound
Priority: optional
Architecture: ${ARCH}
Installed-Size: ${INSTALLED_SIZE}
Depends: python3 (>= ${PY_MM}), python3 (<< ${PY_NEXT}), ffmpeg, portaudio19-dev
Maintainer: Daniel Rosehill <public@danielrosehill.com>
Homepage: https://github.com/danielrosehill/Voice-Notepad-V3
Description: Voice recording with AI-powered transcription
 Voice Notepad V3 is a desktop application for voice recording with
 AI-powered transcription and cleanup using multimodal models from
 Gemini, OpenAI, and Mistral.
 .
 Features:
  - Real-time voice recording
  - AI transcription with automatic cleanup
  - Voice Activity Detection (silence removal)
  - Transcript history and analytics
  - Global hotkeys
  - Cost tracking
EOF

# Create postinst script
cat > "$INSTALL_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e
# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
fi
# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi
# Rebuild KDE cache for Plasma desktop users
if command -v kbuildsycoca6 &> /dev/null; then
    # Run as each logged-in user to update their KDE cache
    for user_home in /home/*; do
        username=$(basename "$user_home")
        if id "$username" &>/dev/null && [ -d "$user_home/.config" ]; then
            su - "$username" -c "kbuildsycoca6 --noincremental" 2>/dev/null || true
        fi
    done
elif command -v kbuildsycoca5 &> /dev/null; then
    for user_home in /home/*; do
        username=$(basename "$user_home")
        if id "$username" &>/dev/null && [ -d "$user_home/.config" ]; then
            su - "$username" -c "kbuildsycoca5 --noincremental" 2>/dev/null || true
        fi
    done
fi
exit 0
EOF
chmod 755 "$INSTALL_DIR/DEBIAN/postinst"

# Create postrm script
cat > "$INSTALL_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e
# Update icon cache on removal
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi
exit 0
EOF
chmod 755 "$INSTALL_DIR/DEBIAN/postrm"

# Build the package
if [ "$FAST_MODE" = true ]; then
    echo "Building .deb package (fast mode - no compression)..."
    dpkg-deb --build --root-owner-group -Z none "$INSTALL_DIR"
else
    echo "Building .deb package..."
    dpkg-deb --build --root-owner-group "$INSTALL_DIR"
fi

# Move to output directory
OUTPUT_DIR="$PROJECT_ROOT/dist"
mkdir -p "$OUTPUT_DIR"
mv "$BUILD_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" "$OUTPUT_DIR/"

# Clean up build directory
rm -rf "$BUILD_DIR"

echo ""
echo "=== Build Complete ==="
echo ""
echo "Package: $OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "To install, run: ./build.sh --install"
echo ""
