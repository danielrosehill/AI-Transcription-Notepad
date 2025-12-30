"""Shared clipboard utilities for Voice Notepad V3.

Provides Wayland-compatible clipboard operations with Qt fallback.
"""

import logging
import subprocess

from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard using wl-copy (Wayland-native) with Qt fallback.

    Args:
        text: Text to copy to clipboard

    Returns:
        True if copy was successful, False otherwise
    """
    # Try wl-copy first for reliable Wayland clipboard
    try:
        process = subprocess.Popen(
            ["wl-copy"],
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        process.communicate(input=text.encode("utf-8"))
        return True
    except FileNotFoundError:
        logger.debug("wl-copy not found, falling back to Qt clipboard")
    except Exception as e:
        logger.debug(f"wl-copy failed: {e}, falling back to Qt clipboard")

    # Fallback to Qt clipboard
    try:
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        return True
    except Exception as e:
        logger.error(f"Qt clipboard failed: {e}")
        return False


def get_clipboard_text() -> str:
    """Get text from clipboard using wl-paste (Wayland-native) with Qt fallback.

    Returns:
        Clipboard text content, or empty string if clipboard is empty or error
    """
    # Try wl-paste first for reliable Wayland clipboard
    try:
        result = subprocess.run(
            ["wl-paste", "--no-newline"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        logger.debug("wl-paste not found, falling back to Qt clipboard")
    except subprocess.TimeoutExpired:
        logger.debug("wl-paste timed out, falling back to Qt clipboard")
    except Exception as e:
        logger.debug(f"wl-paste failed: {e}, falling back to Qt clipboard")

    # Fallback to Qt clipboard
    try:
        clipboard = QApplication.clipboard()
        return clipboard.text() or ""
    except Exception as e:
        logger.error(f"Qt clipboard read failed: {e}")
        return ""
