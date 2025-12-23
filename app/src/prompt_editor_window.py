"""
Unified Prompt Editor Window

A single window for all prompt configuration using a tabbed interface:
1. Foundation - view/edit base system prompt
2. Favorites - star formats for quick buttons
3. Stacks - create element-based stacks
4. Style - formality, verbosity, optional checkboxes
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QScrollArea, QFrame, QCheckBox,
    QGroupBox, QRadioButton, QButtonGroup, QComboBox,
    QGridLayout, QSizePolicy, QMessageBox, QLineEdit,
    QDialog, QDialogButtonBox, QToolButton, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
from typing import List, Set

from .config import (
    Config, save_config,
    FOUNDATION_PROMPT_SECTIONS,
    FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES, FORMAT_CATEGORIES,
    OPTIONAL_PROMPT_COMPONENTS,
    FORMALITY_DISPLAY_NAMES, VERBOSITY_DISPLAY_NAMES
)
from .prompt_elements import (
    FORMAT_ELEMENTS, STYLE_ELEMENTS, GRAMMAR_ELEMENTS,
    PromptStack, get_all_stacks, save_custom_stack, delete_stack,
    build_prompt_from_elements
)


class FormatFavoriteCard(QFrame):
    """A card for a format preset with star toggle."""

    favorite_toggled = pyqtSignal(str, bool)  # format_key, is_favorite
    format_selected = pyqtSignal(str)  # format_key

    def __init__(self, format_key: str, format_data: dict, is_favorite: bool = False, parent=None):
        super().__init__(parent)
        self.format_key = format_key
        self.is_favorite = is_favorite

        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            FormatFavoriteCard {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px;
            }
            FormatFavoriteCard:hover {
                background-color: #e9ecef;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Star button
        self.star_btn = QToolButton()
        self.star_btn.setText("★" if is_favorite else "☆")
        self.star_btn.setStyleSheet(f"""
            QToolButton {{
                border: none;
                font-size: 18px;
                color: {'#ffc107' if is_favorite else '#adb5bd'};
                padding: 2px;
            }}
            QToolButton:hover {{
                color: #ffc107;
            }}
        """)
        self.star_btn.clicked.connect(self._toggle_favorite)
        layout.addWidget(self.star_btn)

        # Format name
        name = FORMAT_DISPLAY_NAMES.get(format_key, format_key)
        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(name_label)

        layout.addStretch()

    def _toggle_favorite(self):
        """Toggle favorite status."""
        self.is_favorite = not self.is_favorite
        self.star_btn.setText("★" if self.is_favorite else "☆")
        self.star_btn.setStyleSheet(f"""
            QToolButton {{
                border: none;
                font-size: 18px;
                color: {'#ffc107' if self.is_favorite else '#adb5bd'};
                padding: 2px;
            }}
            QToolButton:hover {{
                color: #ffc107;
            }}
        """)
        self.favorite_toggled.emit(self.format_key, self.is_favorite)

    def set_favorite(self, is_favorite: bool):
        """Set favorite state without emitting signal."""
        self.is_favorite = is_favorite
        self.star_btn.setText("★" if is_favorite else "☆")
        self.star_btn.setStyleSheet(f"""
            QToolButton {{
                border: none;
                font-size: 18px;
                color: {'#ffc107' if is_favorite else '#adb5bd'};
                padding: 2px;
            }}
            QToolButton:hover {{
                color: #ffc107;
            }}
        """)


class PromptEditorWindow(QMainWindow):
    """Unified window for all prompt configuration."""

    # Signal emitted when favorites change (main window should update quick buttons)
    favorites_changed = pyqtSignal(list)  # List of favorite format keys

    def __init__(self, config: Config, config_dir: Path, parent=None):
        super().__init__(parent)
        self.config = config
        self.config_dir = config_dir

        self.setWindowTitle("Prompts")
        self.setMinimumSize(700, 800)
        self.resize(750, 900)

        # Track UI elements
        self.format_cards = {}  # format_key -> FormatFavoriteCard
        self.element_checkboxes = {}  # element_key -> QCheckBox
        self.selected_elements: Set[str] = set()

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI with a tabbed interface."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header
        header = QLabel("Prompts")
        header.setFont(QFont("Sans", 18, QFont.Weight.Bold))
        main_layout.addWidget(header)

        desc = QLabel(
            "Configure how your transcriptions are processed. "
            "Foundation settings are always applied. Star formats to add them to quick buttons."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6c757d; margin-bottom: 8px;")
        main_layout.addWidget(desc)

        # Tabbed interface
        self.tabs = QTabWidget()

        # Tab 1: Foundation Prompt
        foundation_tab = QWidget()
        foundation_layout = QVBoxLayout(foundation_tab)
        foundation_layout.setContentsMargins(12, 12, 12, 12)
        self._create_foundation_content(foundation_layout)
        foundation_layout.addStretch()
        self.tabs.addTab(foundation_tab, "Foundation")

        # Tab 2: Format Favorites
        favorites_tab = QWidget()
        favorites_scroll = QScrollArea()
        favorites_scroll.setWidgetResizable(True)
        favorites_scroll.setFrameShape(QFrame.Shape.NoFrame)
        favorites_content = QWidget()
        favorites_layout = QVBoxLayout(favorites_content)
        favorites_layout.setContentsMargins(12, 12, 12, 12)
        self._create_favorites_content(favorites_layout)
        favorites_layout.addStretch()
        favorites_scroll.setWidget(favorites_content)
        favorites_tab_layout = QVBoxLayout(favorites_tab)
        favorites_tab_layout.setContentsMargins(0, 0, 0, 0)
        favorites_tab_layout.addWidget(favorites_scroll)
        self.tabs.addTab(favorites_tab, "Favorites")

        # Tab 3: Stack Builder
        stacks_tab = QWidget()
        stacks_layout = QVBoxLayout(stacks_tab)
        stacks_layout.setContentsMargins(12, 12, 12, 12)
        self._create_stack_content(stacks_layout)
        stacks_layout.addStretch()
        self.tabs.addTab(stacks_tab, "Stacks")

        # Tab 4: Tone & Style
        style_tab = QWidget()
        style_layout = QVBoxLayout(style_tab)
        style_layout.setContentsMargins(12, 12, 12, 12)
        self._create_tone_content(style_layout)
        style_layout.addStretch()
        self.tabs.addTab(style_tab, "Style")

        main_layout.addWidget(self.tabs, stretch=1)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(36)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 8px 24px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        close_btn.clicked.connect(self.close)
        main_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _create_foundation_content(self, parent_layout):
        """Create the Foundation Prompt content for the tab."""
        desc = QLabel(
            "These rules are always applied to every transcription. "
            "They define the core cleanup behavior."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6c757d; font-size: 11px; margin-bottom: 8px;")
        parent_layout.addWidget(desc)

        # Build foundation prompt text
        foundation_text = self._build_foundation_display()

        self.foundation_text = QTextEdit()
        self.foundation_text.setPlainText(foundation_text)
        self.foundation_text.setReadOnly(True)
        self.foundation_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        parent_layout.addWidget(self.foundation_text, 1)  # Give it stretch

        # Edit/Reset buttons (disabled for now - read-only)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        info_label = QLabel("Foundation prompt is read-only")
        info_label.setStyleSheet("color: #6c757d; font-size: 10px; font-style: italic;")
        btn_layout.addWidget(info_label)

        parent_layout.addLayout(btn_layout)

    def _build_foundation_display(self) -> str:
        """Build a formatted display of the foundation prompt."""
        lines = []
        for section_key, section_data in FOUNDATION_PROMPT_SECTIONS.items():
            lines.append(f"## {section_data['heading']}")
            for instruction in section_data['instructions']:
                # Truncate long instructions
                if len(instruction) > 120:
                    instruction = instruction[:117] + "..."
                lines.append(f"• {instruction}")
            lines.append("")
        return "\n".join(lines)

    def _create_favorites_content(self, parent_layout):
        """Create the Format Favorites content for the tab."""
        desc = QLabel(
            "Star formats to add them to the quick buttons in the main window. "
            "Starred formats appear as buttons for one-click selection."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6c757d; font-size: 11px; margin-bottom: 8px;")
        parent_layout.addWidget(desc)

        # Format cards by category
        for category_key, category_name in FORMAT_CATEGORIES.items():
            formats_in_category = [
                (k, v) for k, v in FORMAT_TEMPLATES.items()
                if v.get("category") == category_key
            ]
            if not formats_in_category:
                continue

            # Category label
            cat_label = QLabel(category_name)
            cat_label.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 8px;")
            parent_layout.addWidget(cat_label)

            # Grid of format cards
            grid = QGridLayout()
            grid.setSpacing(8)

            for i, (format_key, format_data) in enumerate(formats_in_category):
                is_fav = format_key in self.config.favorite_formats
                card = FormatFavoriteCard(format_key, format_data, is_fav)
                card.favorite_toggled.connect(self._on_favorite_toggled)
                self.format_cards[format_key] = card

                row = i // 3
                col = i % 3
                grid.addWidget(card, row, col)

            parent_layout.addLayout(grid)

    def _on_favorite_toggled(self, format_key: str, is_favorite: bool):
        """Handle favorite toggle."""
        if is_favorite:
            if format_key not in self.config.favorite_formats:
                self.config.favorite_formats.append(format_key)
        else:
            if format_key in self.config.favorite_formats:
                self.config.favorite_formats.remove(format_key)

        save_config(self.config)
        self.favorites_changed.emit(self.config.favorite_formats)

    def _create_stack_content(self, parent_layout):
        """Create the Stack Builder content for the tab."""
        desc = QLabel(
            "Build custom prompt stacks by combining format, style, and grammar elements. "
            "Save stacks for reuse."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6c757d; font-size: 11px; margin-bottom: 8px;")
        parent_layout.addWidget(desc)

        # Stack selector
        stack_row = QHBoxLayout()
        stack_row.addWidget(QLabel("Load Stack:"))

        self.stack_combo = QComboBox()
        self.stack_combo.setMinimumWidth(180)
        self._load_stacks_into_combo()
        self.stack_combo.currentIndexChanged.connect(self._on_stack_selected)
        stack_row.addWidget(self.stack_combo)

        save_btn = QPushButton("Save Stack")
        save_btn.clicked.connect(self._save_current_stack)
        stack_row.addWidget(save_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("color: #dc3545;")
        delete_btn.clicked.connect(self._delete_current_stack)
        stack_row.addWidget(delete_btn)

        stack_row.addStretch()
        parent_layout.addLayout(stack_row)

        # Element checkboxes by category
        elements_container = QWidget()
        elements_layout = QHBoxLayout(elements_container)
        elements_layout.setContentsMargins(0, 8, 0, 0)
        elements_layout.setSpacing(16)

        # Format elements
        format_group = self._create_element_group("Format", FORMAT_ELEMENTS)
        elements_layout.addWidget(format_group)

        # Style elements
        style_group = self._create_element_group("Style", STYLE_ELEMENTS)
        elements_layout.addWidget(style_group)

        # Grammar elements
        grammar_group = self._create_element_group("Grammar", GRAMMAR_ELEMENTS)
        elements_layout.addWidget(grammar_group)

        parent_layout.addWidget(elements_container)

        # Preview button
        preview_btn = QPushButton("Preview Stack Prompt")
        preview_btn.clicked.connect(self._preview_stack)
        parent_layout.addWidget(preview_btn)

    def _create_element_group(self, title: str, elements: dict) -> QGroupBox:
        """Create a group box for element checkboxes."""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(4)

        for key, element in elements.items():
            checkbox = QCheckBox(element.name)
            checkbox.setProperty("element_key", key)
            checkbox.setToolTip(element.description)
            checkbox.stateChanged.connect(self._on_element_toggled)
            self.element_checkboxes[key] = checkbox
            layout.addWidget(checkbox)

        group.setLayout(layout)
        return group

    def _load_stacks_into_combo(self):
        """Load all stacks into the combo box."""
        self.stack_combo.clear()
        self.stack_combo.addItem("-- Select Stack --", None)

        all_stacks = get_all_stacks(self.config_dir)
        for stack in all_stacks:
            self.stack_combo.addItem(stack.name, stack)

    def _on_stack_selected(self, index: int):
        """Handle stack selection."""
        stack = self.stack_combo.currentData()
        if stack is None:
            return

        # Apply the stack
        for key, checkbox in self.element_checkboxes.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(key in stack.elements)
            checkbox.blockSignals(False)

        self.selected_elements = set(stack.elements)

    def _on_element_toggled(self):
        """Handle element checkbox toggle."""
        self.selected_elements.clear()
        for key, checkbox in self.element_checkboxes.items():
            if checkbox.isChecked():
                self.selected_elements.add(key)

        # Reset combo to "Select Stack"
        self.stack_combo.blockSignals(True)
        self.stack_combo.setCurrentIndex(0)
        self.stack_combo.blockSignals(False)

    def _save_current_stack(self):
        """Save the current element selection as a stack."""
        if not self.selected_elements:
            QMessageBox.warning(
                self, "No Elements",
                "Please select at least one element before saving."
            )
            return

        # Get name from user
        dialog = QDialog(self)
        dialog.setWindowTitle("Save Stack")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Stack Name:"))

        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g., Quick Email, Dev Notes")
        layout.addWidget(name_edit)

        layout.addWidget(QLabel("Description (optional):"))
        desc_edit = QLineEdit()
        layout.addWidget(desc_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Name Required", "Please enter a stack name.")
                return

            stack = PromptStack(
                name=name,
                elements=list(self.selected_elements),
                description=desc_edit.text().strip()
            )
            save_custom_stack(stack, self.config_dir)
            self._load_stacks_into_combo()

            QMessageBox.information(
                self, "Stack Saved",
                f"Stack '{name}' has been saved."
            )

    def _delete_current_stack(self):
        """Delete the currently selected stack."""
        stack = self.stack_combo.currentData()
        if stack is None:
            QMessageBox.warning(self, "No Stack Selected", "Please select a stack to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete stack '{stack.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            delete_stack(stack.name, self.config_dir)
            self._load_stacks_into_combo()

    def _preview_stack(self):
        """Preview the generated prompt from current elements."""
        if not self.selected_elements:
            QMessageBox.warning(
                self, "No Elements",
                "Please select elements to preview."
            )
            return

        prompt = build_prompt_from_elements(list(self.selected_elements))

        dialog = QDialog(self)
        dialog.setWindowTitle("Stack Prompt Preview")
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        text = QTextEdit()
        text.setPlainText(prompt)
        text.setReadOnly(True)
        text.setStyleSheet("font-family: monospace; font-size: 11px;")
        layout.addWidget(text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _create_tone_content(self, parent_layout):
        """Create the Tone & Style content for the tab."""
        desc = QLabel(
            "Configure writing tone, verbosity, and optional enhancements."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6c757d; font-size: 11px; margin-bottom: 8px;")
        parent_layout.addWidget(desc)

        # Formality
        formality_row = QHBoxLayout()
        formality_row.addWidget(QLabel("Formality:"))

        self.formality_group = QButtonGroup(self)
        for formality_key, display_name in FORMALITY_DISPLAY_NAMES.items():
            radio = QRadioButton(display_name)
            radio.setProperty("formality_key", formality_key)
            if formality_key == self.config.formality_level:
                radio.setChecked(True)
            self.formality_group.addButton(radio)
            formality_row.addWidget(radio)
        self.formality_group.buttonClicked.connect(self._on_tone_changed)

        formality_row.addStretch()
        parent_layout.addLayout(formality_row)

        # Verbosity
        verbosity_row = QHBoxLayout()
        verbosity_row.addWidget(QLabel("Verbosity Reduction:"))

        self.verbosity_combo = QComboBox()
        self.verbosity_combo.setMinimumWidth(150)
        for verbosity_key in ["none", "minimum", "short", "medium", "maximum"]:
            self.verbosity_combo.addItem(VERBOSITY_DISPLAY_NAMES[verbosity_key], verbosity_key)
        idx = self.verbosity_combo.findData(self.config.verbosity_reduction)
        if idx >= 0:
            self.verbosity_combo.setCurrentIndex(idx)
        self.verbosity_combo.currentIndexChanged.connect(self._on_tone_changed)

        verbosity_row.addWidget(self.verbosity_combo)
        verbosity_row.addStretch()
        parent_layout.addLayout(verbosity_row)

        # Optional enhancements (only the 2 remaining)
        if OPTIONAL_PROMPT_COMPONENTS:
            parent_layout.addWidget(QLabel("Optional Enhancements:"))

            self.optional_checkboxes = {}
            for field_name, _, ui_description in OPTIONAL_PROMPT_COMPONENTS:
                checkbox = QCheckBox(ui_description)
                checkbox.setChecked(getattr(self.config, field_name, False))
                checkbox.stateChanged.connect(
                    lambda state, fn=field_name: self._on_optional_changed(fn, state)
                )
                self.optional_checkboxes[field_name] = checkbox
                parent_layout.addWidget(checkbox)

        # Writing sample
        parent_layout.addWidget(QLabel("Writing Sample (optional):"))
        ws_desc = QLabel(
            "Provide a sample of your writing to guide the AI's output style."
        )
        ws_desc.setStyleSheet("color: #6c757d; font-size: 10px;")
        parent_layout.addWidget(ws_desc)

        self.writing_sample_edit = QTextEdit()
        self.writing_sample_edit.setPlaceholderText(
            "Paste a sample of your writing here..."
        )
        self.writing_sample_edit.setMaximumHeight(120)
        self.writing_sample_edit.setText(self.config.writing_sample)
        self.writing_sample_edit.textChanged.connect(self._on_writing_sample_changed)
        parent_layout.addWidget(self.writing_sample_edit)

    def _on_tone_changed(self):
        """Handle formality or verbosity change."""
        # Update formality
        for button in self.formality_group.buttons():
            if button.isChecked():
                self.config.formality_level = button.property("formality_key")
                break

        # Update verbosity
        self.config.verbosity_reduction = self.verbosity_combo.currentData()

        save_config(self.config)

    def _on_optional_changed(self, field_name: str, state: int):
        """Handle optional checkbox change."""
        setattr(self.config, field_name, state == Qt.CheckState.Checked.value)
        save_config(self.config)

    def _on_writing_sample_changed(self):
        """Handle writing sample change."""
        self.config.writing_sample = self.writing_sample_edit.toPlainText()
        save_config(self.config)
