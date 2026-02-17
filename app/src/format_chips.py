"""Quick Format Bar Widget

An always-visible row of toggleable chip buttons for common format presets.
Includes a [+ More] button that opens a grouped menu with all 31+ formats
and custom prompts from the PromptLibrary.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QMenu,
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction

try:
    from .config import (
        FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES, FORMAT_CATEGORIES, FORMAT_ICONS,
    )
    from .prompt_library import PromptLibrary
except ImportError:
    from config import (
        FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES, FORMAT_CATEGORIES, FORMAT_ICONS,
    )
    from prompt_library import PromptLibrary


def _icon_label(key: str, label: str) -> str:
    """Prepend the emoji icon for a format key to its label."""
    icon = FORMAT_ICONS.get(key, "")
    return f"{icon} {label}" if icon else label


# Default chips shown in the bar (key, label)
_QUICK_CHIPS = [
    ("general", "General"),
    ("email", "Email"),
    ("ai_prompt", "AI Prompt"),
    ("todo", "To-Do"),
    ("meeting_notes", "Notes"),
]

# Labels with icons for quick chips
_QUICK_CHIP_LABELS = {key: _icon_label(key, label) for key, label in _QUICK_CHIPS}

_CHIP_STYLE = """
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 4px 14px;
        font-size: 11px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {hover_bg};
        border-color: {hover_border};
    }}
"""

_CHIP_INACTIVE = _CHIP_STYLE.format(
    bg="#f0f1f3", fg="#495057", border="#dee2e6",
    hover_bg="#e2e6ea", hover_border="#adb5bd",
)

_CHIP_ACTIVE = _CHIP_STYLE.format(
    bg="#0d6efd", fg="white", border="#0d6efd",
    hover_bg="#0b5ed7", hover_border="#0a58ca",
)

_MORE_STYLE = """
    QPushButton {
        background-color: transparent;
        color: #6c757d;
        border: 1px dashed #ced4da;
        border-radius: 12px;
        padding: 4px 10px;
        font-size: 11px;
    }
    QPushButton:hover {
        background-color: #f8f9fa;
        color: #495057;
        border-color: #adb5bd;
    }
    QPushButton::menu-indicator {
        width: 0;
        height: 0;
    }
"""


class QuickFormatBar(QWidget):
    """Always-visible row of format chip buttons."""

    format_changed = pyqtSignal(str)  # Emits the selected format key

    def __init__(self, prompt_library: PromptLibrary = None, parent=None):
        super().__init__(parent)
        self._active_format = "general"
        self._prompt_library = prompt_library
        self._chip_buttons: dict[str, QPushButton] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Quick chips
        for key, label in _QUICK_CHIPS:
            btn = QPushButton(_QUICK_CHIP_LABELS[key])
            btn.setCursor(self.cursor())
            btn.setStyleSheet(_CHIP_INACTIVE)
            btn.clicked.connect(lambda checked, k=key: self._on_chip_clicked(k))
            self._chip_buttons[key] = btn
            layout.addWidget(btn)

        # "+ More" button with dropdown menu
        self._more_btn = QPushButton("+ More")
        self._more_btn.setStyleSheet(_MORE_STYLE)
        self._more_menu = self._build_more_menu()
        self._more_btn.setMenu(self._more_menu)
        layout.addWidget(self._more_btn)

        layout.addStretch()

        # Highlight the default
        self._update_styles()

    def _build_more_menu(self) -> QMenu:
        """Build a grouped QMenu with all formats + custom prompts."""
        menu = QMenu(self)
        quick_keys = {chip[0] for chip in _QUICK_CHIPS}

        # Build category -> [(key, display_name)] mapping
        cat_items: dict[str, list[tuple[str, str]]] = {}
        for key, tmpl in FORMAT_TEMPLATES.items():
            if key in quick_keys or key == "general":
                continue
            category = tmpl.get("category", "other") if isinstance(tmpl, dict) else "other"
            display = FORMAT_DISPLAY_NAMES.get(key, key)
            cat_items.setdefault(category, []).append((key, display))

        # Sort within categories
        for items in cat_items.values():
            items.sort(key=lambda x: x[1])

        # Add to menu by category
        for cat_key, cat_label in FORMAT_CATEGORIES.items():
            items = cat_items.get(cat_key, [])
            if not items:
                continue
            # Foundational items shown at top level, skip "general" (it's a chip)
            if cat_key == "foundational":
                for key, display in items:
                    action = menu.addAction(_icon_label(key, display))
                    action.triggered.connect(
                        lambda checked, k=key: self._on_format_selected(k)
                    )
                menu.addSeparator()
                continue

            submenu = menu.addMenu(cat_label)
            for key, display in items:
                action = submenu.addAction(_icon_label(key, display))
                action.triggered.connect(
                    lambda checked, k=key: self._on_format_selected(k)
                )

        # Custom prompts from library
        if self._prompt_library:
            custom_formats = self._prompt_library.get_custom_by_type("format")
            if custom_formats:
                menu.addSeparator()
                custom_menu = menu.addMenu("Custom")
                for prompt in custom_formats:
                    action = custom_menu.addAction(f"\u2726 {prompt.name}")
                    action.triggered.connect(
                        lambda checked, pid=prompt.id: self._on_format_selected(
                            f"custom:{pid}"
                        )
                    )

        return menu

    def _on_chip_clicked(self, key: str):
        """Handle a quick chip being clicked."""
        if key == self._active_format:
            # Clicking active format resets to General
            if key != "general":
                self._active_format = "general"
                self._update_styles()
                self.format_changed.emit("general")
            return
        self._active_format = key
        self._update_styles()
        self.format_changed.emit(key)

    def _on_format_selected(self, key: str):
        """Handle a format selected from the More menu."""
        self._active_format = key
        self._update_styles()
        self.format_changed.emit(key)

    def _update_styles(self):
        for key, btn in self._chip_buttons.items():
            btn.setStyleSheet(
                _CHIP_ACTIVE if key == self._active_format else _CHIP_INACTIVE
            )

    # ── Public API ────────────────────────────────────────────────

    def get_active_format(self) -> str:
        return self._active_format

    def set_active_format(self, key: str):
        """Programmatically set the active format (e.g., from config load)."""
        self._active_format = key
        self._update_styles()

    def refresh_custom_prompts(self):
        """Rebuild the More menu (e.g., after prompts are edited)."""
        self._more_menu = self._build_more_menu()
        self._more_btn.setMenu(self._more_menu)
