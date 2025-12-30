"""
Unified Prompt Editor Window

A single window for all prompt configuration using a tabbed interface:
1. Prompts - browse and edit all prompts (builtin + custom)
2. Foundation - view base system prompt
3. Stacks - create element-based stacks
4. Style - formality, verbosity, optional checkboxes
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QScrollArea, QFrame, QCheckBox,
    QGroupBox, QRadioButton, QButtonGroup, QComboBox,
    QGridLayout, QSizePolicy, QMessageBox, QLineEdit,
    QDialog, QDialogButtonBox, QToolButton, QTabWidget,
    QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
from typing import List, Set, Optional

from .config import (
    Config, save_config,
    FOUNDATION_PROMPT_SECTIONS,
    FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES, FORMAT_CATEGORIES,
    TONE_TEMPLATES, STYLE_TEMPLATES,
    OPTIONAL_PROMPT_COMPONENTS,
    FORMALITY_DISPLAY_NAMES, VERBOSITY_DISPLAY_NAMES,
    TONE_DISPLAY_NAMES, STYLE_DISPLAY_NAMES
)
from .prompt_elements import (
    FORMAT_ELEMENTS, STYLE_ELEMENTS, GRAMMAR_ELEMENTS,
    PromptStack, get_all_stacks, save_custom_stack, delete_stack,
    build_prompt_from_elements
)
from .prompt_library import (
    PromptLibrary, PromptConfig, PromptConfigCategory, PromptType,
    PROMPT_CONFIG_CATEGORY_NAMES, PROMPT_TYPE_DISPLAY_NAMES
)


class PromptEditDialog(QDialog):
    """Dialog for editing a prompt configuration."""

    def __init__(self, prompt: Optional[PromptConfig] = None, prompt_type: str = "format", parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.is_new = prompt is None
        self.initial_type = prompt.prompt_type if prompt else prompt_type

        self.setWindowTitle("New Prompt" if self.is_new else f"Edit: {prompt.name}")
        self.setMinimumSize(500, 550)
        self.resize(550, 650)

        self._init_ui()
        if prompt:
            self._load_prompt()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Prompt Type (Format, Tone, Style)
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        for ptype in PromptType:
            self.type_combo.addItem(PROMPT_TYPE_DISPLAY_NAMES.get(ptype, ptype.value), ptype.value)
        # Set initial type
        idx = self.type_combo.findData(self.initial_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Type description
        self.type_desc = QLabel("")
        self.type_desc.setWordWrap(True)
        self.type_desc.setStyleSheet("color: #6c757d; font-size: 10px; font-style: italic;")
        layout.addWidget(self.type_desc)

        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Quick Email, Dev Notes")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Category (only for format prompts)
        self.category_container = QWidget()
        cat_layout = QHBoxLayout(self.category_container)
        cat_layout.setContentsMargins(0, 0, 0, 0)
        cat_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        for cat in PromptConfigCategory:
            if cat.value not in ("stylistic", "todo_lists", "blog"):  # Skip legacy
                self.category_combo.addItem(
                    PROMPT_CONFIG_CATEGORY_NAMES.get(cat, cat.value),
                    cat.value
                )
        cat_layout.addWidget(self.category_combo)
        cat_layout.addStretch()
        layout.addWidget(self.category_container)

        # Description
        layout.addWidget(QLabel("Description:"))
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Brief description of what this prompt does")
        layout.addWidget(self.desc_edit)

        # Instruction
        self.instruction_label = QLabel("Format Instruction:")
        layout.addWidget(self.instruction_label)
        self.instruction_edit = QTextEdit()
        self.instruction_edit.setPlaceholderText(
            "Describe how the output should be formatted.\n"
            "e.g., 'Format as a professional email with greeting and sign-off.'"
        )
        self.instruction_edit.setMaximumHeight(100)
        layout.addWidget(self.instruction_edit)

        # Adherence (only for format prompts)
        self.adherence_container = QWidget()
        adherence_layout = QVBoxLayout(self.adherence_container)
        adherence_layout.setContentsMargins(0, 0, 0, 0)
        adherence_layout.addWidget(QLabel("Adherence Guidelines (optional):"))
        self.adherence_edit = QTextEdit()
        self.adherence_edit.setPlaceholderText(
            "Additional guidelines for how strictly to follow the format.\n"
            "e.g., 'Use proper email etiquette. Include a subject line suggestion.'"
        )
        self.adherence_edit.setMaximumHeight(100)
        adherence_layout.addWidget(self.adherence_edit)
        layout.addWidget(self.adherence_container)

        # Formality override (only for format prompts)
        self.formality_container = QWidget()
        formality_layout = QHBoxLayout(self.formality_container)
        formality_layout.setContentsMargins(0, 0, 0, 0)
        formality_layout.addWidget(QLabel("Formality Override:"))
        self.formality_combo = QComboBox()
        self.formality_combo.addItem("Use Global Setting", "")
        for key, display in TONE_DISPLAY_NAMES.items():
            self.formality_combo.addItem(display, key)
        formality_layout.addWidget(self.formality_combo)
        formality_layout.addStretch()
        layout.addWidget(self.formality_container)

        # Verbosity override (only for format prompts)
        self.verbosity_container = QWidget()
        verbosity_layout = QHBoxLayout(self.verbosity_container)
        verbosity_layout.setContentsMargins(0, 0, 0, 0)
        verbosity_layout.addWidget(QLabel("Verbosity Override:"))
        self.verbosity_combo = QComboBox()
        self.verbosity_combo.addItem("Use Global Setting", "")
        for key, display in VERBOSITY_DISPLAY_NAMES.items():
            self.verbosity_combo.addItem(display, key)
        verbosity_layout.addWidget(self.verbosity_combo)
        verbosity_layout.addStretch()
        layout.addWidget(self.verbosity_container)

        layout.addStretch()

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Update UI based on type
        self._on_type_changed()

    def _on_type_changed(self):
        """Update UI based on selected prompt type."""
        prompt_type = self.type_combo.currentData()

        # Update description text based on type
        type_descriptions = {
            "format": "Format prompts define output structure (email, todo list, meeting notes, etc.)",
            "tone": "Tone prompts set the emotional register (casual, professional, friendly, etc.)",
            "style": "Style prompts are writing modifiers that can be combined (concise, persuasive, etc.)",
        }
        self.type_desc.setText(type_descriptions.get(prompt_type, ""))

        # Update instruction label
        instruction_labels = {
            "format": "Format Instruction:",
            "tone": "Tone Instruction:",
            "style": "Style Instruction:",
        }
        self.instruction_label.setText(instruction_labels.get(prompt_type, "Instruction:"))

        # Update placeholders
        placeholders = {
            "format": (
                "Describe how the output should be formatted.\n"
                "e.g., 'Format as a professional email with greeting and sign-off.'"
            ),
            "tone": (
                "Describe the tone/formality to use.\n"
                "e.g., 'Use a warm, friendly, approachable tone that puts the reader at ease.'"
            ),
            "style": (
                "Describe the writing style modifier.\n"
                "e.g., 'Be extremely brief and economical with words. Every word must earn its place.'"
            ),
        }
        self.instruction_edit.setPlaceholderText(placeholders.get(prompt_type, ""))

        # Show/hide sections based on type
        is_format = prompt_type == "format"
        self.category_container.setVisible(is_format)
        self.adherence_container.setVisible(is_format)
        self.formality_container.setVisible(is_format)
        self.verbosity_container.setVisible(is_format)

    def _load_prompt(self):
        """Load prompt data into fields."""
        # Prompt type
        idx = self.type_combo.findData(self.prompt.prompt_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)

        self.name_edit.setText(self.prompt.name)
        self.desc_edit.setText(self.prompt.description)
        self.instruction_edit.setPlainText(self.prompt.instruction)
        self.adherence_edit.setPlainText(self.prompt.adherence)

        # Category
        idx = self.category_combo.findData(self.prompt.category)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)

        # Formality
        if self.prompt.formality:
            idx = self.formality_combo.findData(self.prompt.formality)
            if idx >= 0:
                self.formality_combo.setCurrentIndex(idx)

        # Verbosity
        if self.prompt.verbosity:
            idx = self.verbosity_combo.findData(self.prompt.verbosity)
            if idx >= 0:
                self.verbosity_combo.setCurrentIndex(idx)

        # Update visibility based on loaded type
        self._on_type_changed()

    def _on_save(self):
        """Validate and accept."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Name Required", "Please enter a prompt name.")
            return
        self.accept()

    def get_prompt_data(self) -> dict:
        """Get the edited prompt data."""
        prompt_type = self.type_combo.currentData()
        data = {
            "name": self.name_edit.text().strip(),
            "prompt_type": prompt_type,
            "description": self.desc_edit.text().strip(),
            "instruction": self.instruction_edit.toPlainText().strip(),
        }
        # Only include format-specific fields for format prompts
        if prompt_type == "format":
            data["category"] = self.category_combo.currentData()
            data["adherence"] = self.adherence_edit.toPlainText().strip()
            data["formality"] = self.formality_combo.currentData() or None
            data["verbosity"] = self.verbosity_combo.currentData() or None
        else:
            data["category"] = PromptConfigCategory.CUSTOM.value
            data["adherence"] = ""
            data["formality"] = None
            data["verbosity"] = None
        return data


class PromptEditorWindow(QMainWindow):
    """Unified window for all prompt configuration."""

    # Signal emitted when prompts change (main window should refresh search)
    prompts_changed = pyqtSignal()

    def __init__(self, config: Config, config_dir: Path, parent=None):
        super().__init__(parent)
        self.config = config
        self.config_dir = config_dir
        self.library = PromptLibrary(config_dir)

        self.setWindowTitle("Prompt Manager")
        self.setMinimumSize(800, 700)
        self.resize(900, 800)

        # Track UI elements
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
        header = QLabel("Prompt Manager")
        header.setFont(QFont("Sans", 18, QFont.Weight.Bold))
        main_layout.addWidget(header)

        desc = QLabel(
            "Manage your prompts. Create custom prompts, edit existing ones, "
            "or view the foundation settings that are always applied."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6c757d; margin-bottom: 8px;")
        main_layout.addWidget(desc)

        # Tabbed interface
        self.tabs = QTabWidget()

        # Tab 1: Prompts List
        prompts_tab = QWidget()
        prompts_layout = QVBoxLayout(prompts_tab)
        prompts_layout.setContentsMargins(12, 12, 12, 12)
        self._create_prompts_content(prompts_layout)
        self.tabs.addTab(prompts_tab, "Prompts")

        # Tab 2: Foundation Prompt
        foundation_tab = QWidget()
        foundation_layout = QVBoxLayout(foundation_tab)
        foundation_layout.setContentsMargins(12, 12, 12, 12)
        self._create_foundation_content(foundation_layout)
        foundation_layout.addStretch()
        self.tabs.addTab(foundation_tab, "Foundation")

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

    def _create_prompts_content(self, parent_layout):
        """Create the Prompts content with three sections: Format, Tone, Style."""
        desc = QLabel(
            "Manage prompts organized by type. Format prompts define output structure, "
            "Tone prompts set formality, and Style prompts are combinable writing modifiers."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6c757d; font-size: 11px; margin-bottom: 8px;")
        parent_layout.addWidget(desc)

        # Create scroll area for sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        # Track section widgets
        self.section_lists = {}  # prompt_type -> QListWidget
        self.section_buttons = {}  # prompt_type -> dict of buttons

        # Create three sections
        for prompt_type, section_title, section_desc in [
            ("format", "Format Prompts", "Define output structure (email, todo list, meeting notes, etc.)"),
            ("tone", "Tone Prompts", "Set formality and emotional register (casual, professional, friendly, etc.)"),
            ("style", "Style Prompts", "Stackable writing modifiers (concise, persuasive, analytical, etc.)"),
        ]:
            section = self._create_prompt_section(prompt_type, section_title, section_desc)
            scroll_layout.addWidget(section)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        parent_layout.addWidget(scroll, stretch=1)

        # Populate all sections
        self._populate_all_sections()

    def _create_prompt_section(self, prompt_type: str, title: str, description: str) -> QFrame:
        """Create a collapsible section for a prompt type."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header row with title and add button
        header = QHBoxLayout()

        title_label = QLabel(f"<b>{title}</b>")
        title_label.setStyleSheet("font-size: 13px; border: none; background: transparent;")
        header.addWidget(title_label)

        desc_label = QLabel(f"— {description}")
        desc_label.setStyleSheet("color: #6c757d; font-size: 11px; border: none; background: transparent;")
        header.addWidget(desc_label)

        header.addStretch()

        # Add button
        add_btn = QPushButton(f"+ Add {title.replace(' Prompts', '')}")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_btn.clicked.connect(lambda: self._create_new_prompt(prompt_type))
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Splitter for list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter { border: none; background: transparent; }")

        # Prompt list
        list_widget = QListWidget()
        list_widget.setMinimumHeight(120)
        list_widget.setMaximumHeight(180)
        list_widget.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 4px 8px;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        list_widget.currentItemChanged.connect(
            lambda curr, prev: self._on_section_prompt_selected(prompt_type, curr)
        )
        self.section_lists[prompt_type] = list_widget
        splitter.addWidget(list_widget)

        # Details panel
        details = QWidget()
        details.setStyleSheet("background: transparent; border: none;")
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(8, 0, 0, 0)
        details_layout.setSpacing(4)

        # Details labels (will be updated on selection)
        details_name = QLabel("Select a prompt")
        details_name.setStyleSheet("font-weight: bold; font-size: 12px; border: none;")
        details_name.setProperty("detail_type", "name")
        details_layout.addWidget(details_name)

        details_desc = QLabel("")
        details_desc.setWordWrap(True)
        details_desc.setStyleSheet("color: #666; font-size: 11px; border: none;")
        details_desc.setProperty("detail_type", "desc")
        details_layout.addWidget(details_desc)

        details_instruction = QLabel("")
        details_instruction.setWordWrap(True)
        details_instruction.setStyleSheet("font-size: 10px; color: #444; font-style: italic; border: none;")
        details_instruction.setProperty("detail_type", "instruction")
        details_layout.addWidget(details_instruction)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        edit_btn = QPushButton("Edit")
        edit_btn.setEnabled(False)
        edit_btn.setMaximumWidth(60)
        edit_btn.clicked.connect(lambda: self._edit_section_prompt(prompt_type))
        btn_row.addWidget(edit_btn)

        dup_btn = QPushButton("Duplicate")
        dup_btn.setEnabled(False)
        dup_btn.setMaximumWidth(70)
        dup_btn.clicked.connect(lambda: self._duplicate_section_prompt(prompt_type))
        btn_row.addWidget(dup_btn)

        del_btn = QPushButton("Delete")
        del_btn.setEnabled(False)
        del_btn.setMaximumWidth(60)
        del_btn.setStyleSheet("color: #dc3545;")
        del_btn.clicked.connect(lambda: self._delete_section_prompt(prompt_type))
        btn_row.addWidget(del_btn)

        btn_row.addStretch()
        details_layout.addLayout(btn_row)

        details_layout.addStretch()
        splitter.addWidget(details)

        splitter.setSizes([200, 300])
        layout.addWidget(splitter)

        # Store button references
        self.section_buttons[prompt_type] = {
            "edit": edit_btn,
            "duplicate": dup_btn,
            "delete": del_btn,
            "details_name": details_name,
            "details_desc": details_desc,
            "details_instruction": details_instruction,
        }

        return section

    def _populate_all_sections(self):
        """Populate all three prompt sections."""
        for prompt_type in ["format", "tone", "style"]:
            self._populate_section(prompt_type)

    def _populate_section(self, prompt_type: str):
        """Populate a single section's list with prompts of that type."""
        list_widget = self.section_lists.get(prompt_type)
        if list_widget is None:
            return

        list_widget.clear()

        # Get builtin prompts for this type
        builtins = self._get_builtin_prompts_for_type(prompt_type)
        # Get custom prompts for this type
        custom_prompts = self.library.get_custom_by_type(prompt_type)

        # Get IDs of custom prompts (some may override builtins)
        custom_ids = {p.id for p in custom_prompts}

        # Add builtins that haven't been overridden by custom versions
        unmodified_builtins = [p for p in builtins if p.id not in custom_ids]
        for prompt in sorted(unmodified_builtins, key=lambda p: p.name.lower()):
            item = QListWidgetItem()
            item.setText(prompt.name)
            item.setData(Qt.ItemDataRole.UserRole, prompt.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, "builtin")
            list_widget.addItem(item)

        # Add separator if we have both unmodified builtins and custom
        if unmodified_builtins and custom_prompts:
            separator = QListWidgetItem("── Custom / Edited ──")
            separator.setFlags(Qt.ItemFlag.NoItemFlags)
            separator.setForeground(Qt.GlobalColor.gray)
            list_widget.addItem(separator)

        # Add custom prompts (includes edited builtins)
        for prompt in sorted(custom_prompts, key=lambda p: p.name.lower()):
            item = QListWidgetItem()
            item.setText(prompt.name)
            item.setData(Qt.ItemDataRole.UserRole, prompt.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, "custom")
            list_widget.addItem(item)

    def _get_builtin_prompts_for_type(self, prompt_type: str) -> list:
        """Get builtin prompts that should appear in a section.

        For 'format': Uses the existing FORMAT_TEMPLATES from config
        For 'tone': Uses TONE_TEMPLATES from config
        For 'style': Uses STYLE_TEMPLATES from config
        """
        prompts = []

        if prompt_type == "format":
            # Create PromptConfig objects from FORMAT_TEMPLATES
            for key, display_name in FORMAT_DISPLAY_NAMES.items():
                template_data = FORMAT_TEMPLATES.get(key, {})
                if isinstance(template_data, dict):
                    instruction = template_data.get("instruction", "")
                    adherence = template_data.get("adherence", "")
                else:
                    instruction = template_data if template_data else ""
                    adherence = ""

                prompts.append(PromptConfig(
                    id=f"builtin_format_{key}",
                    name=display_name,
                    category=PromptConfigCategory.CUSTOM.value,
                    description=f"Format as {display_name.lower()}",
                    prompt_type="format",
                    instruction=instruction,
                    adherence=adherence,
                    is_builtin=True,
                ))

        elif prompt_type == "tone":
            # Create PromptConfig objects from TONE_TEMPLATES
            for key, display_name in TONE_DISPLAY_NAMES.items():
                instruction = TONE_TEMPLATES.get(key, "")
                prompts.append(PromptConfig(
                    id=f"builtin_tone_{key}",
                    name=display_name,
                    category=PromptConfigCategory.CUSTOM.value,
                    description=f"{display_name} tone",
                    prompt_type="tone",
                    instruction=instruction,
                    is_builtin=True,
                ))

        elif prompt_type == "style":
            # Create PromptConfig objects from STYLE_TEMPLATES
            for key, display_name in STYLE_DISPLAY_NAMES.items():
                instruction = STYLE_TEMPLATES.get(key, "")
                prompts.append(PromptConfig(
                    id=f"builtin_style_{key}",
                    name=display_name,
                    category=PromptConfigCategory.CUSTOM.value,
                    description=f"{display_name} writing style",
                    prompt_type="style",
                    instruction=instruction,
                    is_builtin=True,
                ))

        return prompts

    def _on_section_prompt_selected(self, prompt_type: str, current):
        """Handle prompt selection in a section."""
        buttons = self.section_buttons.get(prompt_type, {})
        if not buttons:
            return

        if current is None or not current.flags():
            # No selection or separator selected
            buttons["details_name"].setText("Select a prompt")
            buttons["details_desc"].setText("")
            buttons["details_instruction"].setText("")
            buttons["edit"].setEnabled(False)
            buttons["duplicate"].setEnabled(False)
            buttons["delete"].setEnabled(False)
            return

        prompt_id = current.data(Qt.ItemDataRole.UserRole)
        source = current.data(Qt.ItemDataRole.UserRole + 1)

        # Get prompt (either from library or builtin)
        if source == "builtin":
            # Get from our generated builtins
            builtins = self._get_builtin_prompts_for_type(prompt_type)
            prompt = next((p for p in builtins if p.id == prompt_id), None)
        else:
            prompt = self.library.get(prompt_id)

        if not prompt:
            return

        # Update details
        buttons["details_name"].setText(prompt.name)
        buttons["details_desc"].setText(prompt.description or "No description")

        instruction_preview = prompt.instruction[:150] + "..." if len(prompt.instruction) > 150 else prompt.instruction
        buttons["details_instruction"].setText(instruction_preview or "(No instruction)")

        # Enable/disable buttons
        is_custom = source == "custom"
        buttons["edit"].setEnabled(True)  # Can edit both builtin (as modification) and custom
        buttons["duplicate"].setEnabled(True)
        buttons["delete"].setEnabled(is_custom)  # Can only delete custom

    def _edit_section_prompt(self, prompt_type: str):
        """Edit the selected prompt in a section."""
        list_widget = self.section_lists.get(prompt_type)
        if list_widget is None:
            return

        current = list_widget.currentItem()
        if not current or not current.flags():
            return

        prompt_id = current.data(Qt.ItemDataRole.UserRole)
        source = current.data(Qt.ItemDataRole.UserRole + 1)

        if source == "builtin":
            # Get builtin prompt
            builtins = self._get_builtin_prompts_for_type(prompt_type)
            prompt = next((p for p in builtins if p.id == prompt_id), None)
            if not prompt:
                return
        else:
            prompt = self.library.get(prompt_id)
            if not prompt:
                return

        dialog = PromptEditDialog(prompt, prompt_type, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_prompt_data()

            if source == "builtin":
                # For builtins, create a custom prompt that overrides it
                # Keep the same ID so it effectively replaces the builtin
                edited_prompt = PromptConfig(
                    id=prompt_id,  # Same ID to override
                    name=data["name"],
                    category=data.get("category", PromptConfigCategory.CUSTOM.value),
                    description=data["description"],
                    prompt_type=data["prompt_type"],
                    instruction=data["instruction"],
                    adherence=data.get("adherence", ""),
                    formality=data.get("formality"),
                    verbosity=data.get("verbosity"),
                    is_builtin=False,  # Now a custom prompt
                )
                self.library.create_custom(edited_prompt)
            else:
                # Update existing custom prompt
                prompt.name = data["name"]
                prompt.prompt_type = data["prompt_type"]
                prompt.description = data["description"]
                prompt.instruction = data["instruction"]
                prompt.category = data.get("category", PromptConfigCategory.CUSTOM.value)
                prompt.adherence = data.get("adherence", "")
                prompt.formality = data.get("formality")
                prompt.verbosity = data.get("verbosity")
                self.library.update_custom(prompt)

            self._populate_all_sections()
            self.prompts_changed.emit()

    def _duplicate_section_prompt(self, prompt_type: str):
        """Duplicate the selected prompt as a new custom prompt."""
        list_widget = self.section_lists.get(prompt_type)
        if list_widget is None:
            return

        current = list_widget.currentItem()
        if not current or not current.flags():
            return

        prompt_id = current.data(Qt.ItemDataRole.UserRole)
        source = current.data(Qt.ItemDataRole.UserRole + 1)

        if source == "builtin":
            builtins = self._get_builtin_prompts_for_type(prompt_type)
            prompt = next((p for p in builtins if p.id == prompt_id), None)
        else:
            prompt = self.library.get(prompt_id)

        if not prompt:
            return

        new_prompt = prompt.clone(f"{prompt.name} (Custom)")
        new_prompt.prompt_type = prompt_type  # Ensure type is preserved
        self.library.create_custom(new_prompt)
        self._populate_all_sections()
        self.prompts_changed.emit()

        QMessageBox.information(
            self, "Prompt Duplicated",
            f"Created '{new_prompt.name}' as a custom copy."
        )

    def _delete_section_prompt(self, prompt_type: str):
        """Delete the selected custom prompt."""
        list_widget = self.section_lists.get(prompt_type)
        if list_widget is None:
            return

        current = list_widget.currentItem()
        if not current or not current.flags():
            return

        prompt_id = current.data(Qt.ItemDataRole.UserRole)
        source = current.data(Qt.ItemDataRole.UserRole + 1)

        if source == "builtin":
            return  # Can't delete builtins

        prompt = self.library.get(prompt_id)
        if not prompt:
            return

        # Check if this is an edited builtin (ID starts with builtin_)
        is_edited_builtin = prompt_id.startswith("builtin_")

        if is_edited_builtin:
            reply = QMessageBox.question(
                self, "Restore Original?",
                f"This will delete your edits to '{prompt.name}' and restore the original built-in version.\n\nContinue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        else:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Delete prompt '{prompt.name}'?\n\nThis cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

        if reply == QMessageBox.StandardButton.Yes:
            self.library.delete_custom(prompt_id)
            self._populate_all_sections()
            self.prompts_changed.emit()

    def _create_new_prompt(self, prompt_type: str = "format"):
        """Create a new custom prompt of the specified type."""
        dialog = PromptEditDialog(prompt_type=prompt_type, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_prompt_data()

            prompt = PromptConfig(
                id="",  # Will be auto-generated
                name=data["name"],
                category=data.get("category", PromptConfigCategory.CUSTOM.value),
                description=data["description"],
                prompt_type=data["prompt_type"],
                instruction=data["instruction"],
                adherence=data.get("adherence", ""),
                formality=data.get("formality"),
                verbosity=data.get("verbosity"),
                is_builtin=False,
            )

            self.library.create_custom(prompt)
            self._populate_all_sections()
            self.prompts_changed.emit()

            type_name = PROMPT_TYPE_DISPLAY_NAMES.get(PromptType(data["prompt_type"]), data["prompt_type"])
            QMessageBox.information(
                self, "Prompt Created",
                f"{type_name} prompt '{data['name']}' has been created."
            )

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
                lines.append(f"* {instruction}")
            lines.append("")
        return "\n".join(lines)

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
