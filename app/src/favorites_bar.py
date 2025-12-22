"""Favorites Bar Widget

A dynamic button bar for quick access to favorite prompt configurations.
Supports up to 20 favorites across multiple rows.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QButtonGroup, QLabel, QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
from typing import Optional, List, Callable

try:
    from .prompt_library import PromptLibrary, PromptConfig
except ImportError:
    from prompt_library import PromptLibrary, PromptConfig


class FavoritesBar(QWidget):
    """Dynamic button bar for favorite prompt configurations.

    Features:
    - Displays favorites as clickable buttons
    - Supports up to 20 buttons across multiple rows
    - Mutual exclusivity (only one selected at a time)
    - Automatic refresh when favorites change
    """

    # Emitted when a prompt is selected (prompt_id)
    prompt_selected = pyqtSignal(str)

    # Emitted when "Manage" button is clicked
    manage_clicked = pyqtSignal()

    # Maximum buttons per row
    BUTTONS_PER_ROW = 5

    # Maximum total favorites
    MAX_FAVORITES = 20

    def __init__(self, config_dir: Path, parent=None):
        super().__init__(parent)
        self.config_dir = config_dir
        self.library = PromptLibrary(config_dir)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.buttons: dict[str, QPushButton] = {}  # prompt_id -> button

        self._current_prompt_id: Optional[str] = None

        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        """Set up the UI layout."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

        # Container for button rows
        self.buttons_container = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_container)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(4)

        self.main_layout.addWidget(self.buttons_container)

        # Bottom row with Manage button
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 4, 0, 0)

        # Spacer to align with buttons (for "Format:" label if present)
        bottom_row.addSpacing(70)

        self.manage_btn = QPushButton("Manage Prompts...")
        self.manage_btn.setFixedHeight(28)
        self.manage_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 11px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        self.manage_btn.clicked.connect(self.manage_clicked.emit)
        bottom_row.addWidget(self.manage_btn)

        bottom_row.addStretch()
        self.main_layout.addLayout(bottom_row)

    def refresh(self):
        """Refresh the button bar from the library."""
        # Clear existing buttons
        for btn in self.buttons.values():
            self.button_group.removeButton(btn)
            btn.deleteLater()
        self.buttons.clear()

        # Clear existing row layouts
        while self.buttons_layout.count():
            item = self.buttons_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                item.layout().deleteLater()

        # Get favorites
        favorites = self.library.get_favorites()[:self.MAX_FAVORITES]

        if not favorites:
            # Show placeholder
            placeholder = QLabel("No favorites. Click 'Manage Prompts' to add some.")
            placeholder.setStyleSheet("color: #6c757d; font-style: italic;")
            self.buttons_layout.addWidget(placeholder)
            return

        # Create buttons in rows
        current_row = None
        buttons_in_row = 0

        for i, prompt in enumerate(favorites):
            # Start new row if needed
            if buttons_in_row == 0 or buttons_in_row >= self.BUTTONS_PER_ROW:
                current_row = QHBoxLayout()
                current_row.setSpacing(8)

                # First row gets "Format:" label
                if i == 0:
                    label = QLabel("Format:")
                    label.setStyleSheet("font-weight: bold; color: #495057;")
                    label.setFixedWidth(60)
                    current_row.addWidget(label)
                else:
                    # Align with first row
                    current_row.addSpacing(68)

                self.buttons_layout.addLayout(current_row)
                buttons_in_row = 0

            # Create button
            btn = self._create_button(prompt)
            self.buttons[prompt.id] = btn
            self.button_group.addButton(btn)
            current_row.addWidget(btn)
            buttons_in_row += 1

        # Add stretch to last row
        if current_row:
            current_row.addStretch()

        # Restore selection
        if self._current_prompt_id and self._current_prompt_id in self.buttons:
            self.buttons[self._current_prompt_id].setChecked(True)
        elif favorites:
            # Default to first favorite
            self._current_prompt_id = favorites[0].id
            self.buttons[self._current_prompt_id].setChecked(True)

    def _create_button(self, prompt: PromptConfig) -> QPushButton:
        """Create a format button for a prompt."""
        btn = QPushButton(prompt.name)
        btn.setCheckable(True)
        btn.setMinimumHeight(32)
        btn.setToolTip(prompt.description)

        # Connect click
        btn.clicked.connect(lambda checked, pid=prompt.id: self._on_button_clicked(pid))

        # Style
        btn.setStyleSheet("""
            QPushButton {
                background-color: #cfe2ff;
                color: #000000;
                border: 2px solid #9ec5fe;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                padding: 4px 12px;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #b6d4fe;
                border-color: #86b7fe;
            }
            QPushButton:checked {
                background-color: #28a745;
                color: white;
                border-color: #28a745;
            }
            QPushButton:checked:hover {
                background-color: #218838;
                border-color: #1e7e34;
            }
        """)

        return btn

    def _on_button_clicked(self, prompt_id: str):
        """Handle button click."""
        self._current_prompt_id = prompt_id
        self.prompt_selected.emit(prompt_id)

    def get_selected_prompt_id(self) -> Optional[str]:
        """Get the currently selected prompt ID."""
        return self._current_prompt_id

    def set_selected_prompt_id(self, prompt_id: str):
        """Set the selected prompt by ID."""
        self._current_prompt_id = prompt_id
        if prompt_id in self.buttons:
            self.buttons[prompt_id].setChecked(True)

    def get_selected_prompt(self) -> Optional[PromptConfig]:
        """Get the currently selected prompt config."""
        if self._current_prompt_id:
            return self.library.get(self._current_prompt_id)
        return None

    def update_library(self):
        """Reload the library and refresh display."""
        self.library = PromptLibrary(self.config_dir)
        self.refresh()
