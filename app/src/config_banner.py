"""Config Summary Banner Widget

An always-visible horizontal row of clickable pill badges showing the active
configuration at a glance: format, tones, styles, output modes, VAD,
translation, personalize/date/TLDR.

Clicking a pill either toggles a boolean setting or signals the parent to
open the relevant Customize panel section.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

try:
    from .config import (
        Config,
        FORMAT_DISPLAY_NAMES,
        FORMAT_ICONS,
        TONE_DISPLAY_NAMES,
        STYLE_DISPLAY_NAMES,
        get_language_display_name,
        get_language_flag,
    )
except ImportError:
    from config import (
        Config,
        FORMAT_DISPLAY_NAMES,
        FORMAT_ICONS,
        TONE_DISPLAY_NAMES,
        STYLE_DISPLAY_NAMES,
        get_language_display_name,
        get_language_flag,
    )


# Pill styles
_PILL_HIGHLIGHTED = """
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 2px 10px;
        font-size: 10px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {hover};
    }}
"""

_PILL_MUTED = """
    QPushButton {
        background-color: #f0f1f3;
        color: #6c757d;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 2px 10px;
        font-size: 10px;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #e2e6ea;
    }
"""


def _blue_pill():
    return _PILL_HIGHLIGHTED.format(
        bg="#e7f1ff", fg="#0d6efd", border="#b6d4fe", hover="#d0e3ff"
    )


def _green_pill():
    return _PILL_HIGHLIGHTED.format(
        bg="#d1e7dd", fg="#198754", border="#a3cfbb", hover="#bddcce"
    )


def _purple_pill():
    return _PILL_HIGHLIGHTED.format(
        bg="#e8daef", fg="#6f42c1", border="#c9a9e0", hover="#dbc9ea"
    )


def _teal_pill():
    return _PILL_HIGHLIGHTED.format(
        bg="#d1ecf1", fg="#0c5460", border="#bee5eb", hover="#c0dfe5"
    )


def _orange_pill():
    return _PILL_HIGHLIGHTED.format(
        bg="#fff3cd", fg="#856404", border="#ffeeba", hover="#ffecb5"
    )


class ConfigSummaryBanner(QWidget):
    """Horizontal row of clickable pill badges showing active config."""

    # Signal: (category, key) - e.g. ("format", "email"), ("toggle", "vad")
    setting_clicked = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pills: list[QPushButton] = []
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 2, 4, 2)
        self._layout.setSpacing(4)
        self._layout.addStretch()  # placeholder

    def update_from_config(self, config: Config):
        """Rebuild all pills from the current config state."""
        # Remove old pills
        for pill in self._pills:
            self._layout.removeWidget(pill)
            pill.deleteLater()
        self._pills.clear()

        # Remove old stretch items
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        pills_data = []  # (label, style, category, key)

        # Format (always show, even for "general")
        fmt = getattr(config, 'format_preset', 'general')
        display = FORMAT_DISPLAY_NAMES.get(fmt, fmt)
        icon = FORMAT_ICONS.get(fmt, "")
        label = f"{icon} {display}".strip() if icon else display
        if fmt == "verbatim":
            pills_data.append((label, _blue_pill(), "base", "verbatim"))
        else:
            pills_data.append((label, _blue_pill() if fmt != "general" else _PILL_MUTED, "format", fmt))

        # Selected formats (multi-select from stack builder)
        selected_formats = getattr(config, 'selected_formats', [])
        for fkey in selected_formats:
            display = FORMAT_DISPLAY_NAMES.get(fkey, fkey)
            icon = FORMAT_ICONS.get(fkey, "")
            label = f"{icon} {display}".strip() if icon else display
            pills_data.append((label, _blue_pill(), "format", fkey))

        # Tones
        selected_tones = getattr(config, 'selected_tones', [])
        for tkey in selected_tones:
            display = TONE_DISPLAY_NAMES.get(tkey, tkey)
            pills_data.append((display, _purple_pill(), "tone", tkey))

        # Legacy formality level (if not neutral and no selected_tones)
        if not selected_tones:
            formality = getattr(config, 'formality_level', 'neutral')
            if formality != "neutral":
                display = TONE_DISPLAY_NAMES.get(formality, formality)
                pills_data.append((display, _purple_pill(), "tone", formality))

        # Styles
        selected_styles = getattr(config, 'selected_styles', [])
        for skey in selected_styles:
            display = STYLE_DISPLAY_NAMES.get(skey, skey)
            pills_data.append((display, _teal_pill(), "style", skey))

        # VAD
        if getattr(config, 'vad_enabled', False):
            pills_data.append(("VAD", _green_pill(), "toggle", "vad"))

        # Output modes (only show non-default)
        if getattr(config, 'output_to_clipboard', False):
            pills_data.append(("Clipboard", _green_pill(), "toggle", "clipboard"))
        if getattr(config, 'output_to_inject', False):
            pills_data.append(("Inject", _green_pill(), "toggle", "inject"))
        if not getattr(config, 'output_to_app', True):
            pills_data.append(("No App", _PILL_MUTED, "toggle", "app"))

        # Translation
        if getattr(config, 'translation_mode_enabled', False):
            lang = getattr(config, 'translation_target_language', '')
            flag = get_language_flag(lang) if lang else ""
            name = get_language_display_name(lang) if lang else "Translation"
            label = f"{flag} {name}".strip() if flag else name
            pills_data.append((label, _orange_pill(), "base", "translation"))

        # Extras
        if getattr(config, 'personalization_enabled', False):
            pills_data.append(("Personalize", _teal_pill(), "extra", "personalize"))
        if getattr(config, 'add_date_enabled', False):
            pills_data.append(("Date", _teal_pill(), "extra", "date"))
        if getattr(config, 'tldr_enabled', False):
            pills_data.append(("TLDR", _teal_pill(), "extra", "tldr"))

        # Build pill buttons
        for label, style, category, key in pills_data:
            pill = QPushButton(label)
            pill.setStyleSheet(style)
            pill.setCursor(Qt.CursorShape.PointingHandCursor)
            pill.setSizePolicy(
                QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
            )
            pill.clicked.connect(
                lambda checked, c=category, k=key: self.setting_clicked.emit(c, k)
            )
            self._layout.addWidget(pill)
            self._pills.append(pill)

        self._layout.addStretch()

        # Always visible (at minimum shows the format pill)
        self.setVisible(True)
