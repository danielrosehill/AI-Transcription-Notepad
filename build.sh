#!/bin/bash
# Build a Debian package for Voice Notepad V3
# Output: dist/voice-notepad_VERSION_amd64.deb

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Version from argument or default
VERSION="${1:-1.1.0}"
PACKAGE_NAME="voice-notepad"
ARCH="amd64"

echo "=== Building Voice Notepad V3 - v${VERSION} ==="
echo ""

# Build directory
BUILD_DIR="$SCRIPT_DIR/build/deb"
INSTALL_DIR="$BUILD_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}"

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$INSTALL_DIR"

# Create directory structure
mkdir -p "$INSTALL_DIR/DEBIAN"
mkdir -p "$INSTALL_DIR/opt/voice-notepad"
mkdir -p "$INSTALL_DIR/usr/bin"
mkdir -p "$INSTALL_DIR/usr/share/applications"
mkdir -p "$INSTALL_DIR/usr/share/icons/hicolor/128x128/apps"

echo "Creating virtual environment and installing dependencies..."

# Create venv using uv with system Python (not uv-managed)
uv venv "$INSTALL_DIR/opt/voice-notepad/.venv" --python /usr/bin/python3 --seed
source "$INSTALL_DIR/opt/voice-notepad/.venv/bin/activate"

# Install dependencies using uv
uv pip install -r app/requirements.txt

# Copy source files
echo "Copying application files..."
cp -r app/src "$INSTALL_DIR/opt/voice-notepad/"
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

# Create a simple icon (SVG microphone)
cat > "$INSTALL_DIR/usr/share/icons/hicolor/128x128/apps/voice-notepad.svg" << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#dc3545">
  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
</svg>
EOF

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
Depends: python3 (>= 3.10), python3-venv, ffmpeg, portaudio19-dev
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
echo "Building .deb package..."
deactivate 2>/dev/null || true
dpkg-deb --build --root-owner-group "$INSTALL_DIR"

# Move to output directory
OUTPUT_DIR="$SCRIPT_DIR/dist"
mkdir -p "$OUTPUT_DIR"
mv "$BUILD_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" "$OUTPUT_DIR/"

# Clean up build directory
rm -rf "$BUILD_DIR"

echo ""
echo "=== Build Complete ==="
echo ""
echo "Package: $OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "To install, run: ./install.sh"
echo ""
