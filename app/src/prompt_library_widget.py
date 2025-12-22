"""Prompt Library Tab UI

A unified interface for managing prompt configurations:
- Browse all prompts (builtins + custom) by category
- Edit prompt details (instruction, adherence, etc.)
- Manage favorites for quick access
- Create custom prompts
- Clone and modify builtin prompts
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit,
    QTextEdit, QPlainTextEdit, QPushButton, QGroupBox,
    QFormLayout, QComboBox, QCheckBox, QMessageBox,
    QInputDialog, QFrame, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path

try:
    from .prompt_library import (
        PromptLibrary, PromptConfig, PromptConfigCategory,
        PROMPT_CONFIG_CATEGORY_NAMES, build_prompt_from_config,
    )
except ImportError:
    from prompt_library import (
        PromptLibrary, PromptConfig, PromptConfigCategory,
        PROMPT_CONFIG_CATEGORY_NAMES, build_prompt_from_config,
    )


class PromptLibraryWidget(QWidget):
    """Widget for browsing and managing prompt configurations."""

    # Emitted when favorites change (for updating quick-access bar)
    favorites_changed = pyqtSignal()

    # Emitted when a prompt is selected (for preview)
    prompt_selected = pyqtSignal(str)  # prompt_id

    def __init__(self, config_dir: Path, parent=None):
        super().__init__(parent)
        self.config_dir = config_dir
        self.library = PromptLibrary(config_dir)
        self.current_prompt_id = None

        self._setup_ui()
        self._load_prompts()

    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel: prompt list
        left_panel = self._create_list_panel()
        splitter.addWidget(left_panel)

        # Right panel: details/edit
        right_panel = self._create_details_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions (40% list, 60% details)
        splitter.setSizes([400, 600])

    def _create_list_panel(self) -> QWidget:
        """Create the left panel with prompt list."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 5, 0)

        # Search box
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search prompts...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Prompt tree
        self.prompt_tree = QTreeWidget()
        self.prompt_tree.setHeaderHidden(True)
        self.prompt_tree.setIndentation(20)
        self.prompt_tree.itemClicked.connect(self._on_prompt_selected)
        self.prompt_tree.setMinimumWidth(250)
        layout.addWidget(self.prompt_tree)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self._on_new_prompt)
        btn_layout.addWidget(self.new_btn)

        self.clone_btn = QPushButton("Clone")
        self.clone_btn.clicked.connect(self._on_clone_prompt)
        self.clone_btn.setEnabled(False)
        btn_layout.addWidget(self.clone_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete_prompt)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)

        layout.addLayout(btn_layout)

        return panel

    def _create_details_panel(self) -> QWidget:
        """Create the right panel with prompt details."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 0, 0, 0)

        # Scroll area for details
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Header with name and favorite toggle
        header_layout = QHBoxLayout()

        self.name_label = QLabel("Select a prompt")
        self.name_label.setFont(QFont("", 14, QFont.Weight.Bold))
        header_layout.addWidget(self.name_label)

        header_layout.addStretch()

        self.favorite_btn = QPushButton("Add to Favorites")
        self.favorite_btn.clicked.connect(self._toggle_favorite)
        self.favorite_btn.setEnabled(False)
        header_layout.addWidget(self.favorite_btn)

        scroll_layout.addLayout(header_layout)

        # Description
        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #666;")
        scroll_layout.addWidget(self.description_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        scroll_layout.addWidget(line)

        # Edit form
        form_group = QGroupBox("Prompt Configuration")
        form_layout = QFormLayout(form_group)

        # Name (editable for custom)
        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(self._on_field_changed)
        form_layout.addRow("Name:", self.name_input)

        # Category
        self.category_combo = QComboBox()
        for cat in PromptConfigCategory:
            self.category_combo.addItem(PROMPT_CONFIG_CATEGORY_NAMES[cat], cat.value)
        self.category_combo.currentIndexChanged.connect(self._on_field_changed)
        form_layout.addRow("Category:", self.category_combo)

        # Description
        self.desc_input = QLineEdit()
        self.desc_input.textChanged.connect(self._on_field_changed)
        form_layout.addRow("Description:", self.desc_input)

        # Instruction
        instruction_label = QLabel("Format Instruction:")
        self.instruction_input = QPlainTextEdit()
        self.instruction_input.setMaximumHeight(100)
        self.instruction_input.textChanged.connect(self._on_field_changed)
        form_layout.addRow(instruction_label, self.instruction_input)

        # Adherence
        adherence_label = QLabel("Adherence Rules:")
        self.adherence_input = QPlainTextEdit()
        self.adherence_input.setMaximumHeight(100)
        self.adherence_input.textChanged.connect(self._on_field_changed)
        form_layout.addRow(adherence_label, self.adherence_input)

        scroll_layout.addWidget(form_group)

        # Overrides group
        overrides_group = QGroupBox("Optional Overrides")
        overrides_layout = QFormLayout(overrides_group)

        # Formality override
        self.formality_combo = QComboBox()
        self.formality_combo.addItem("Use global setting", None)
        self.formality_combo.addItem("Casual", "casual")
        self.formality_combo.addItem("Neutral", "neutral")
        self.formality_combo.addItem("Professional", "professional")
        self.formality_combo.currentIndexChanged.connect(self._on_field_changed)
        overrides_layout.addRow("Formality:", self.formality_combo)

        # Verbosity override
        self.verbosity_combo = QComboBox()
        self.verbosity_combo.addItem("Use global setting", None)
        self.verbosity_combo.addItem("None", "none")
        self.verbosity_combo.addItem("Minimum", "minimum")
        self.verbosity_combo.addItem("Short", "short")
        self.verbosity_combo.addItem("Medium", "medium")
        self.verbosity_combo.addItem("Maximum", "maximum")
        self.verbosity_combo.currentIndexChanged.connect(self._on_field_changed)
        overrides_layout.addRow("Verbosity:", self.verbosity_combo)

        # Business signature toggle (for email)
        self.business_sig_check = QCheckBox("Use business signature (vs personal)")
        self.business_sig_check.stateChanged.connect(self._on_field_changed)
        overrides_layout.addRow("Email:", self.business_sig_check)

        scroll_layout.addWidget(overrides_group)

        # Preview group
        preview_group = QGroupBox("Prompt Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_text = QPlainTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setStyleSheet("background-color: #f5f5f5;")
        preview_layout.addWidget(self.preview_text)

        preview_btn = QPushButton("Refresh Preview")
        preview_btn.clicked.connect(self._update_preview)
        preview_layout.addWidget(preview_btn)

        scroll_layout.addWidget(preview_group)

        # Save/Reset buttons
        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)

        self.reset_btn = QPushButton("Reset to Default")
        self.reset_btn.clicked.connect(self._on_reset)
        self.reset_btn.setEnabled(False)
        btn_layout.addWidget(self.reset_btn)

        btn_layout.addStretch()

        scroll_layout.addLayout(btn_layout)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return panel

    def _load_prompts(self):
        """Load prompts into the tree widget."""
        self.prompt_tree.clear()

        # Get all prompts grouped by category
        prompts_by_category = {}
        for prompt in self.library.get_all():
            cat = prompt.category
            if cat not in prompts_by_category:
                prompts_by_category[cat] = []
            prompts_by_category[cat].append(prompt)

        # Add favorites section at top
        favorites = self.library.get_favorites()
        if favorites:
            favorites_item = QTreeWidgetItem(["Favorites"])
            favorites_item.setFont(0, QFont("", -1, QFont.Weight.Bold))
            self.prompt_tree.addTopLevelItem(favorites_item)

            for prompt in favorites:
                child = QTreeWidgetItem([prompt.name])
                child.setData(0, Qt.ItemDataRole.UserRole, prompt.id)
                if prompt.is_modified:
                    child.setText(0, f"{prompt.name} (modified)")
                favorites_item.addChild(child)

            favorites_item.setExpanded(True)

        # Add category sections
        category_order = [
            PromptConfigCategory.GENERAL,
            PromptConfigCategory.WORK,
            PromptConfigCategory.DOCUMENTATION,
            PromptConfigCategory.LISTS,
            PromptConfigCategory.CREATIVE,
            PromptConfigCategory.CUSTOM,
        ]

        for cat in category_order:
            cat_value = cat.value if isinstance(cat, PromptConfigCategory) else cat
            if cat_value not in prompts_by_category:
                continue

            prompts = prompts_by_category[cat_value]
            if not prompts:
                continue

            # Category header
            cat_name = PROMPT_CONFIG_CATEGORY_NAMES.get(cat, cat_value.title())
            cat_item = QTreeWidgetItem([cat_name])
            cat_item.setFont(0, QFont("", -1, QFont.Weight.Bold))
            self.prompt_tree.addTopLevelItem(cat_item)

            # Add prompts
            for prompt in sorted(prompts, key=lambda p: p.name):
                child = QTreeWidgetItem([prompt.name])
                child.setData(0, Qt.ItemDataRole.UserRole, prompt.id)
                if prompt.is_modified:
                    child.setText(0, f"{prompt.name} (modified)")
                if not prompt.is_builtin:
                    child.setText(0, f"{prompt.name} (custom)")
                cat_item.addChild(child)

            cat_item.setExpanded(True)

    def _on_search(self, text: str):
        """Filter prompts by search text."""
        if not text:
            self._load_prompts()
            return

        results = self.library.search(text)

        self.prompt_tree.clear()
        results_item = QTreeWidgetItem([f"Search Results ({len(results)})"])
        results_item.setFont(0, QFont("", -1, QFont.Weight.Bold))
        self.prompt_tree.addTopLevelItem(results_item)

        for prompt in results:
            child = QTreeWidgetItem([prompt.name])
            child.setData(0, Qt.ItemDataRole.UserRole, prompt.id)
            results_item.addChild(child)

        results_item.setExpanded(True)

    def _on_prompt_selected(self, item: QTreeWidgetItem, column: int):
        """Handle prompt selection in the tree."""
        prompt_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not prompt_id:
            return  # Category header clicked

        self.current_prompt_id = prompt_id
        prompt = self.library.get(prompt_id)
        if not prompt:
            return

        self._display_prompt(prompt)
        self.prompt_selected.emit(prompt_id)

    def _display_prompt(self, prompt: PromptConfig):
        """Display prompt details in the edit panel."""
        # Block signals while populating
        self._block_signals(True)

        # Header
        self.name_label.setText(prompt.name)
        self.description_label.setText(prompt.description)

        # Favorite button
        self.favorite_btn.setEnabled(True)
        if prompt.is_favorite:
            self.favorite_btn.setText("Remove from Favorites")
        else:
            self.favorite_btn.setText("Add to Favorites")

        # Form fields
        self.name_input.setText(prompt.name)
        self.name_input.setEnabled(not prompt.is_builtin or prompt.is_modified)

        # Category
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == prompt.category:
                self.category_combo.setCurrentIndex(i)
                break
        self.category_combo.setEnabled(not prompt.is_builtin)

        self.desc_input.setText(prompt.description)
        self.instruction_input.setPlainText(prompt.instruction)
        self.adherence_input.setPlainText(prompt.adherence)

        # Overrides
        self._set_combo_by_data(self.formality_combo, prompt.formality)
        self._set_combo_by_data(self.verbosity_combo, prompt.verbosity)
        self.business_sig_check.setChecked(prompt.use_business_signature)

        # Enable/disable controls
        self.clone_btn.setEnabled(True)
        self.delete_btn.setEnabled(not prompt.is_builtin)
        self.reset_btn.setEnabled(prompt.is_builtin and prompt.is_modified)
        self.save_btn.setEnabled(False)

        self._block_signals(False)

        # Update preview
        self._update_preview()

    def _set_combo_by_data(self, combo: QComboBox, value):
        """Set combo box selection by data value."""
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return
        combo.setCurrentIndex(0)

    def _block_signals(self, block: bool):
        """Block/unblock signals from edit widgets."""
        self.name_input.blockSignals(block)
        self.category_combo.blockSignals(block)
        self.desc_input.blockSignals(block)
        self.instruction_input.blockSignals(block)
        self.adherence_input.blockSignals(block)
        self.formality_combo.blockSignals(block)
        self.verbosity_combo.blockSignals(block)
        self.business_sig_check.blockSignals(block)

    def _on_field_changed(self):
        """Handle changes to edit fields."""
        self.save_btn.setEnabled(True)

    def _update_preview(self):
        """Update the prompt preview."""
        if not self.current_prompt_id:
            return

        # Build a temporary config from current form values
        temp_config = PromptConfig(
            id=self.current_prompt_id,
            name=self.name_input.text(),
            category=self.category_combo.currentData() or PromptConfigCategory.GENERAL,
            description=self.desc_input.text(),
            instruction=self.instruction_input.toPlainText(),
            adherence=self.adherence_input.toPlainText(),
            formality=self.formality_combo.currentData(),
            verbosity=self.verbosity_combo.currentData(),
            use_business_signature=self.business_sig_check.isChecked(),
        )

        # Build and display preview
        preview = build_prompt_from_config(temp_config)
        self.preview_text.setPlainText(preview)

    def _toggle_favorite(self):
        """Toggle favorite status for current prompt."""
        if not self.current_prompt_id:
            return

        prompt = self.library.get(self.current_prompt_id)
        if not prompt:
            return

        if prompt.is_favorite:
            self.library.remove_favorite(self.current_prompt_id)
            self.favorite_btn.setText("Add to Favorites")
        else:
            self.library.add_favorite(self.current_prompt_id)
            self.favorite_btn.setText("Remove from Favorites")

        self._load_prompts()
        self.favorites_changed.emit()

    def _on_new_prompt(self):
        """Create a new custom prompt."""
        name, ok = QInputDialog.getText(
            self, "New Prompt", "Enter prompt name:"
        )
        if not ok or not name:
            return

        config = PromptConfig(
            id="",  # Will be generated
            name=name,
            category=PromptConfigCategory.CUSTOM,
            description="Custom prompt",
            instruction="",
            adherence="",
            is_builtin=False,
        )

        config = self.library.create_custom(config)
        self._load_prompts()

        # Select the new prompt
        self.current_prompt_id = config.id
        self._display_prompt(config)

    def _on_clone_prompt(self):
        """Clone the current prompt."""
        if not self.current_prompt_id:
            return

        prompt = self.library.get(self.current_prompt_id)
        if not prompt:
            return

        name, ok = QInputDialog.getText(
            self, "Clone Prompt", "Enter name for cloned prompt:",
            text=f"{prompt.name} (copy)"
        )
        if not ok or not name:
            return

        cloned = prompt.clone(name)
        cloned = self.library.create_custom(cloned)
        self._load_prompts()

        # Select the cloned prompt
        self.current_prompt_id = cloned.id
        self._display_prompt(cloned)

    def _on_delete_prompt(self):
        """Delete the current custom prompt."""
        if not self.current_prompt_id:
            return

        prompt = self.library.get(self.current_prompt_id)
        if not prompt or prompt.is_builtin:
            return

        reply = QMessageBox.question(
            self, "Delete Prompt",
            f"Are you sure you want to delete '{prompt.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.library.delete_custom(self.current_prompt_id)
        self.current_prompt_id = None
        self._load_prompts()
        self._clear_details()
        self.favorites_changed.emit()

    def _on_save(self):
        """Save changes to the current prompt."""
        if not self.current_prompt_id:
            return

        prompt = self.library.get(self.current_prompt_id)
        if not prompt:
            return

        # Gather form values
        modifications = {
            "name": self.name_input.text(),
            "description": self.desc_input.text(),
            "instruction": self.instruction_input.toPlainText(),
            "adherence": self.adherence_input.toPlainText(),
            "formality": self.formality_combo.currentData(),
            "verbosity": self.verbosity_combo.currentData(),
            "use_business_signature": self.business_sig_check.isChecked(),
        }

        if not prompt.is_builtin:
            # Custom prompt: update directly
            modifications["category"] = self.category_combo.currentData()
            updated = PromptConfig.from_dict({**prompt.to_dict(), **modifications})
            self.library.update_custom(updated)
        else:
            # Builtin: store modifications
            self.library.modify_builtin(self.current_prompt_id, modifications)

        self._load_prompts()
        self.save_btn.setEnabled(False)

        # Refresh display
        updated_prompt = self.library.get(self.current_prompt_id)
        if updated_prompt:
            self._display_prompt(updated_prompt)

    def _on_reset(self):
        """Reset a builtin prompt to its default state."""
        if not self.current_prompt_id:
            return

        prompt = self.library.get(self.current_prompt_id)
        if not prompt or not prompt.is_builtin:
            return

        reply = QMessageBox.question(
            self, "Reset Prompt",
            f"Reset '{prompt.name}' to its default configuration?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.library.reset_builtin(self.current_prompt_id)
        self._load_prompts()

        # Refresh display
        reset_prompt = self.library.get(self.current_prompt_id)
        if reset_prompt:
            self._display_prompt(reset_prompt)

    def _clear_details(self):
        """Clear the details panel."""
        self.name_label.setText("Select a prompt")
        self.description_label.setText("")
        self.name_input.clear()
        self.desc_input.clear()
        self.instruction_input.clear()
        self.adherence_input.clear()
        self.preview_text.clear()
        self.favorite_btn.setEnabled(False)
        self.clone_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)

    def get_favorites(self) -> list:
        """Get list of favorite prompt configs."""
        return self.library.get_favorites()

    def get_prompt(self, prompt_id: str) -> PromptConfig:
        """Get a prompt config by ID."""
        return self.library.get(prompt_id)

    def refresh(self):
        """Refresh the prompt list."""
        self._load_prompts()
