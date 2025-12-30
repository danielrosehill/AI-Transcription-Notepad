"""Shared UI utility functions for Voice Notepad V3.

Contains common icon loading functions used across multiple widgets.
"""

from pathlib import Path

from PyQt6.QtGui import QIcon


def get_icons_dir() -> Path:
    """Get the path to the icons directory."""
    return Path(__file__).parent / "icons"


def get_provider_icon(provider: str) -> QIcon:
    """Get the icon for a given provider.

    Args:
        provider: Provider name (e.g., "openrouter", "gemini", "google")

    Returns:
        QIcon for the provider, or empty QIcon if not found
    """
    icons_dir = get_icons_dir()
    icon_map = {
        "openrouter": "or_icon.png",
        "gemini": "gemini_icon.png",
        "google": "gemini_icon.png",
    }
    icon_filename = icon_map.get(provider.lower(), "")
    if icon_filename:
        icon_path = icons_dir / icon_filename
        if icon_path.exists():
            return QIcon(str(icon_path))
    return QIcon()


def get_model_icon(model_id: str) -> QIcon:
    """Get the icon for a model based on its originator.

    Args:
        model_id: Model identifier (e.g., "google/gemini-2.5-flash", "gemini-flash-latest")

    Returns:
        QIcon for the model, or empty QIcon if not found
    """
    icons_dir = get_icons_dir()
    model_lower = model_id.lower()

    # All models are now Gemini-based
    if model_lower.startswith("google/") or model_lower.startswith("gemini"):
        icon_filename = "gemini_icon.png"
    else:
        return QIcon()

    icon_path = icons_dir / icon_filename
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()
