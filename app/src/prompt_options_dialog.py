"""
Dialog for configuring detailed prompt options.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QCheckBox, QLineEdit, QRadioButton, QButtonGroup,
    QComboBox, QPushButton, QFrame, QCompleter
)
from PyQt6.QtCore import Qt, pyqtSignal
from .config import (
    Config, save_config,
    OPTIONAL_PROMPT_COMPONENTS,
    FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES,
    FORMALITY_DISPLAY_NAMES,
    VERBOSITY_DISPLAY_NAMES,
    EMAIL_SIGNOFFS
)


class PromptOptionsDialog(QDialog):
    """Modal dialog for configuring detailed prompt options."""

    # Signal emitted when settings change
    settings_changed = pyqtSignal()

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("System Prompt Configuration")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._init_ui()

    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Section 1: Optional Enhancements
        enhancements_label = QLabel("<b>Optional Enhancements</b>")
        enhancements_label.setStyleSheet("font-size: 13px; color: #495057;")
        layout.addWidget(enhancements_label)

        # Checkboxes in a grid layout
        checkbox_grid = QGridLayout()
        checkbox_grid.setSpacing(8)
        checkbox_grid.setContentsMargins(8, 4, 8, 4)

        self.prompt_checkboxes = {}
        for i, (field_name, _, ui_description) in enumerate(OPTIONAL_PROMPT_COMPONENTS):
            checkbox = QCheckBox(ui_description)
            checkbox.setStyleSheet("font-size: 11px;")
            checkbox.setChecked(getattr(self.config, field_name, False))
            checkbox.stateChanged.connect(self._on_setting_changed)
            self.prompt_checkboxes[field_name] = checkbox
            row = i // 2
            col = i % 2
            checkbox_grid.addWidget(checkbox, row, col)

        layout.addLayout(checkbox_grid)

        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet("background-color: #dee2e6;")
        separator1.setFixedHeight(1)
        layout.addWidget(separator1)

        # Section 2: Format Settings
        format_label = QLabel("<b>Format Settings</b>")
        format_label.setStyleSheet("font-size: 13px; color: #495057;")
        layout.addWidget(format_label)

        format_form = QFormLayout()
        format_form.setSpacing(8)
        format_form.setContentsMargins(8, 4, 8, 4)

        # Format search field with completer
        self.format_search = QLineEdit()
        self.format_search.setPlaceholderText("Search formats...")

        # Create completer with all format names
        format_names = [FORMAT_DISPLAY_NAMES[key] for key in FORMAT_TEMPLATES.keys()]
        self.format_completer = QCompleter(format_names)
        self.format_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.format_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.format_search.setCompleter(self.format_completer)

        # Set initial text from config
        current_format_name = FORMAT_DISPLAY_NAMES[self.config.format_preset]
        self.format_search.setText(current_format_name)

        # Connect signals
        self.format_search.textChanged.connect(self._on_format_search_changed)
        self.format_completer.activated.connect(self._on_format_selected)

        format_form.addRow("Format:", self.format_search)

        layout.addLayout(format_form)

        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("background-color: #dee2e6;")
        separator2.setFixedHeight(1)
        layout.addWidget(separator2)

        # Section 3: Tone and Style
        tone_label = QLabel("<b>Tone and Style</b>")
        tone_label.setStyleSheet("font-size: 13px; color: #495057;")
        layout.addWidget(tone_label)

        tone_style_layout = QVBoxLayout()
        tone_style_layout.setSpacing(12)
        tone_style_layout.setContentsMargins(8, 4, 8, 4)

        # Formality radio buttons
        formality_row = QHBoxLayout()
        formality_row.addWidget(QLabel("Formality:"))

        self.formality_group = QButtonGroup(self)
        for formality_key, display_name in FORMALITY_DISPLAY_NAMES.items():
            radio = QRadioButton(display_name)
            radio.setStyleSheet("font-size: 11px;")
            radio.setProperty("formality_key", formality_key)
            if formality_key == self.config.formality_level:
                radio.setChecked(True)
            self.formality_group.addButton(radio)
            formality_row.addWidget(radio)
        self.formality_group.buttonClicked.connect(self._on_setting_changed)

        formality_row.addStretch()
        tone_style_layout.addLayout(formality_row)

        # Verbosity dropdown
        verbosity_row = QHBoxLayout()
        verbosity_row.addWidget(QLabel("Verbosity Reduction:"))

        self.verbosity_combo = QComboBox()
        self.verbosity_combo.setMinimumWidth(150)
        for verbosity_key in ["none", "minimum", "short", "medium", "maximum"]:
            self.verbosity_combo.addItem(VERBOSITY_DISPLAY_NAMES[verbosity_key], verbosity_key)
        idx = self.verbosity_combo.findData(self.config.verbosity_reduction)
        if idx >= 0:
            self.verbosity_combo.setCurrentIndex(idx)
        self.verbosity_combo.currentIndexChanged.connect(self._on_setting_changed)

        verbosity_row.addWidget(self.verbosity_combo)
        verbosity_row.addStretch()
        tone_style_layout.addLayout(verbosity_row)

        layout.addLayout(tone_style_layout)

        # Separator
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        separator3.setStyleSheet("background-color: #dee2e6;")
        separator3.setFixedHeight(1)
        layout.addWidget(separator3)

        # Section 4: Email Settings (conditionally visible)
        email_header = QHBoxLayout()
        email_label = QLabel("<b>Email Settings</b>")
        email_label.setStyleSheet("font-size: 13px; color: #495057;")
        email_header.addWidget(email_label)

        email_info = QLabel("(Only used when Email format is selected)")
        email_info.setStyleSheet("font-size: 10px; color: #6c757d; font-style: italic;")
        email_header.addWidget(email_info)
        email_header.addStretch()

        layout.addLayout(email_header)

        # Email settings form
        self.email_settings_frame = QFrame()
        self.email_settings_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        email_form = QFormLayout(self.email_settings_frame)
        email_form.setSpacing(8)
        email_form.setContentsMargins(12, 12, 12, 12)
        email_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Name field
        self.user_name_edit = QLineEdit(self.config.user_name)
        self.user_name_edit.setPlaceholderText("e.g., Daniel Rosehill")
        self.user_name_edit.textChanged.connect(self._on_setting_changed)
        email_form.addRow("Your name:", self.user_name_edit)

        # Email field
        self.user_email_edit = QLineEdit(self.config.user_email)
        self.user_email_edit.setPlaceholderText("e.g., daniel@example.com")
        self.user_email_edit.textChanged.connect(self._on_setting_changed)
        email_form.addRow("Email address:", self.user_email_edit)

        # Phone field
        self.user_phone_edit = QLineEdit(self.config.user_phone)
        self.user_phone_edit.setPlaceholderText("e.g., +972-555-1234")
        self.user_phone_edit.textChanged.connect(self._on_setting_changed)
        email_form.addRow("Phone number:", self.user_phone_edit)

        # Sign-off field
        self.signoff_combo = QComboBox()
        self.signoff_combo.setEditable(True)
        for signoff in EMAIL_SIGNOFFS:
            self.signoff_combo.addItem(signoff)
        idx = self.signoff_combo.findText(self.config.email_signature)
        if idx >= 0:
            self.signoff_combo.setCurrentIndex(idx)
        else:
            self.signoff_combo.setEditText(self.config.email_signature)
        self.signoff_combo.currentTextChanged.connect(self._on_setting_changed)
        email_form.addRow("Email sign-off:", self.signoff_combo)

        layout.addWidget(self.email_settings_frame)

        # Show/hide email settings based on current format
        self._update_email_settings_visibility()

        # Add spacer
        layout.addStretch()

        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setMinimumWidth(100)
        close_btn.setMinimumHeight(32)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _update_email_settings_visibility(self):
        """Show/hide email settings based on format selection."""
        is_email = self.config.format_preset == "email"
        self.email_settings_frame.setVisible(is_email)

    def _on_format_search_changed(self, text: str):
        """Handle format search text changes."""
        # If user types exact match, apply it
        for key, name in FORMAT_DISPLAY_NAMES.items():
            if name.lower() == text.lower():
                self.config.format_preset = key
                save_config(self.config)
                self._update_email_settings_visibility()
                self.settings_changed.emit()
                break

    def _on_format_selected(self, text: str):
        """Handle format selection from completer."""
        for key, name in FORMAT_DISPLAY_NAMES.items():
            if name == text:
                self.config.format_preset = key
                save_config(self.config)
                self._update_email_settings_visibility()
                self.settings_changed.emit()
                break

    def _on_setting_changed(self):
        """Handle any setting change."""
        # Update optional enhancements
        for field_name, checkbox in self.prompt_checkboxes.items():
            setattr(self.config, field_name, checkbox.isChecked())

        # Update formality
        for button in self.formality_group.buttons():
            if button.isChecked():
                self.config.formality_level = button.property("formality_key")
                break

        # Update verbosity
        self.config.verbosity_reduction = self.verbosity_combo.currentData()

        # Update email settings
        self.config.user_name = self.user_name_edit.text()
        self.config.user_email = self.user_email_edit.text()
        self.config.user_phone = self.user_phone_edit.text()
        self.config.email_signature = self.signoff_combo.currentText()

        # Save config
        save_config(self.config)
        self.settings_changed.emit()
