"""Favorites Bar Widget

A dynamic button bar for quick access to favorite prompt configurations.
Uses a linear row layout with favorites grouped by favorite_order.
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
from collections import OrderedDict

try:
    from .prompt_library import PromptLibrary, PromptConfig, PromptConfigCategory, PROMPT_CONFIG_CATEGORY_NAMES
except ImportError:
    from prompt_library import PromptLibrary, PromptConfig, PromptConfigCategory, PROMPT_CONFIG_CATEGORY_NAMES


# Row boundaries based on favorite_order:
# Row 1 (0-9): General, Verbatim
# Row 2 (10-19): Blog Post, Email, Meeting Notes, Documentation
# Row 3 (20-29): AI Prompt, Dev Prompt, System Prompt
# Row 4 (30-39): Note to Self, To-Do List, Shopping List
# Row 5 (40-49): Status Update, Social Post
ROW_BOUNDARIES = [10, 20, 30, 40, 50]  # Cutoff points for each row


class FavoritesBar(QWidget):
    """Dynamic button bar for favorite prompt configurations.

    Features:
    - Linear row layout with favorites grouped by favorite_order
    - Row boundaries: 0-9 (Row 1), 10-19 (Row 2), 20-29 (Row 3), etc.
    - Supports up to 30 buttons total
    - Mutual exclusivity (only one selected at a time)
    - Automatic refresh when favorites change
    """

    # Emitted when a prompt is selected (prompt_id)
    prompt_selected = pyqtSignal(str)

    # Emitted when "Manage" button is clicked
    manage_clicked = pyqtSignal()

    # Maximum total favorites
    MAX_FAVORITES = 30

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
        self.main_layout.setSpacing(6)

        # Container for rows of buttons
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(4)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.main_layout.addWidget(self.rows_container)

        # Bottom row with Manage button
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 4, 0, 0)

        self.manage_btn = QPushButton("Manage Prompts...")
        self.manage_btn.setFixedHeight(26)
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

    def _clear_rows(self):
        """Clear all items from the rows layout."""
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                item.layout().deleteLater()
            elif item.widget():
                item.widget().deleteLater()

    def _get_row_for_order(self, order: int) -> int:
        """Get the row number for a given favorite_order."""
        for i, boundary in enumerate(ROW_BOUNDARIES):
            if order < boundary:
                return i
        return len(ROW_BOUNDARIES)  # Last row for anything beyond boundaries

    def refresh(self):
        """Refresh the button bar from the library, grouped by favorite_order rows."""
        # Clear existing buttons
        for btn in self.buttons.values():
            self.button_group.removeButton(btn)
            btn.deleteLater()
        self.buttons.clear()

        # Clear existing layouts
        self._clear_rows()

        # Get favorites
        favorites = self.library.get_favorites()[:self.MAX_FAVORITES]

        if not favorites:
            # Show placeholder
            placeholder = QLabel("No favorites. Click 'Manage Prompts' to add some.")
            placeholder.setStyleSheet("color: #6c757d; font-style: italic;")
            self.rows_layout.addWidget(placeholder)
            return

        # Group favorites by row based on favorite_order
        rows: dict[int, List[PromptConfig]] = {}
        for prompt in favorites:
            row_num = self._get_row_for_order(prompt.favorite_order)
            if row_num not in rows:
                rows[row_num] = []
            rows[row_num].append(prompt)

        # Create rows in order
        for row_num in sorted(rows.keys()):
            prompts = rows[row_num]
            # Sort prompts within the row by favorite_order
            prompts.sort(key=lambda p: p.favorite_order)

            row_layout = QHBoxLayout()
            row_layout.setSpacing(6)

            for prompt in prompts:
                btn = self._create_button(prompt)
                self.buttons[prompt.id] = btn
                self.button_group.addButton(btn)
                row_layout.addWidget(btn)

            row_layout.addStretch()
            self.rows_layout.addLayout(row_layout)

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
        btn.setMinimumHeight(28)
        btn.setToolTip(prompt.description)

        # Connect click
        btn.clicked.connect(lambda checked, pid=prompt.id: self._on_button_clicked(pid))

        # Compact style for two-column layout
        btn.setStyleSheet("""
            QPushButton {
                background-color: #cfe2ff;
                color: #000000;
                border: 2px solid #9ec5fe;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
                padding: 3px 8px;
                min-width: 60px;
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
