"""Prompt Stack Builder Widget

A visual columnar interface for building prompt stacks on the Record tab.
Replaces FavoritesBar with a more intuitive layer-based approach.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QRadioButton, QCheckBox, QButtonGroup, QLabel,
    QFrame, QComboBox, QPushButton,
    QSizePolicy, QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional, List, Dict, Any

try:
    from .config import (
        Config, TONE_TEMPLATES, TONE_DISPLAY_NAMES,
        STYLE_TEMPLATES, STYLE_DISPLAY_NAMES,
        FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES,
    )
except ImportError:
    from config import (
        Config, TONE_TEMPLATES, TONE_DISPLAY_NAMES,
        STYLE_TEMPLATES, STYLE_DISPLAY_NAMES,
        FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES,
    )


class StackBuilderWidget(QWidget):
    """Visual columnar prompt stack builder.

    Provides a column-based interface for building prompt layers:
    - BASE: General vs Verbatim (mutually exclusive)
    - FORMAT: Output format presets (mutually exclusive)
    - TONE: Formality level (mutually exclusive)
    - STYLE: Writing styles (multi-select, stackable)
    - CONSTRAINTS: Word limits with direction

    Emits prompt_changed signal when any selection changes.
    """

    # Emitted when any setting changes
    prompt_changed = pyqtSignal()

    # Base options (mutually exclusive)
    BASE_OPTIONS = [
        ("general", "General", "Standard cleanup and formatting"),
        ("verbatim", "Verbatim", "Minimal transformation, close to original speech"),
    ]

    # Quick-access format options
    FORMAT_QUICK_OPTIONS = [
        ("none", "None", "No specific format - general cleanup only"),
        ("ai_prompt", "AI Prompt", "Format as an AI prompt"),
        ("email", "Email", "Format as an email with greeting and signature"),
        ("meeting_agenda", "Agenda", "Format as a meeting agenda"),
        ("meeting_minutes", "Minutes", "Format as formal meeting minutes"),
        ("social_post", "Social Post", "Format for social media/community"),
        ("todo", "To-Do", "Format as a to-do list"),
    ]

    # Tone options (mutually exclusive) - quick access for common tones
    TONE_QUICK_OPTIONS = [
        ("neutral", "Neutral", "No specific tone modifier"),
        ("casual", "Casual", "Relaxed, conversational tone"),
        ("professional", "Professional", "Formal business tone"),
        ("friendly", "Friendly", "Warm, approachable tone"),
    ]

    # Additional tones available in dropdown
    TONE_MORE_OPTIONS = [
        ("authoritative", "Authoritative", "Confident, expert tone"),
        ("enthusiastic", "Enthusiastic", "Energetic, excited tone"),
        ("empathetic", "Empathetic", "Understanding, caring tone"),
        ("urgent", "Urgent", "Time-sensitive, pressing tone"),
        ("reassuring", "Reassuring", "Calm, comforting tone"),
    ]

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config

        self._setup_ui()
        self._load_from_config()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the columnar UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Header with reset button
        header_layout = QHBoxLayout()
        header = QLabel("📚 <b>Prompt Stack</b>")
        header.setStyleSheet("font-size: 12px; color: #444; padding: 2px 0;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        self.reset_btn = QPushButton("↺ Reset")
        self.reset_btn.setToolTip("Reset to General with no modifiers")
        self.reset_btn.setMaximumWidth(70)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                color: #666;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        header_layout.addWidget(self.reset_btn)
        main_layout.addLayout(header_layout)

        # Columns container - increased spacing between columns
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)  # More horizontal spacing between columns
        columns_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create each column
        self.base_group = self._create_base_column()
        self.format_group, self.format_combo = self._create_format_column()
        self.tone_group, self.tone_combo = self._create_tone_column()
        self.style_checkboxes = self._create_style_column()

        columns_layout.addWidget(self.base_group)
        columns_layout.addWidget(self.format_group)
        columns_layout.addWidget(self.tone_group)
        columns_layout.addWidget(self._create_style_container())
        columns_layout.addStretch()

        main_layout.addLayout(columns_layout)

    def _create_column_frame(self, title: str) -> QFrame:
        """Create a styled frame for a column."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        return frame

    def _create_base_column(self) -> QGroupBox:
        """Create the BASE column (General vs Verbatim)."""
        group = QGroupBox("Base")
        group.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 12, 6, 6)

        self.base_button_group = QButtonGroup(self)
        self.base_buttons: Dict[str, QRadioButton] = {}

        for key, label, tooltip in self.BASE_OPTIONS:
            radio = QRadioButton(label)
            radio.setToolTip(tooltip)
            radio.setStyleSheet(self._get_radio_style())
            self.base_button_group.addButton(radio)
            self.base_buttons[key] = radio
            layout.addWidget(radio)

        layout.addStretch()
        return group

    def _create_format_column(self) -> tuple:
        """Create the FORMAT column with quick options + dropdown."""
        group = QGroupBox("Format")
        group.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 12, 6, 6)

        self.format_button_group = QButtonGroup(self)
        self.format_buttons: Dict[str, QRadioButton] = {}

        for key, label, tooltip in self.FORMAT_QUICK_OPTIONS:
            radio = QRadioButton(label)
            radio.setToolTip(tooltip)
            radio.setStyleSheet(self._get_radio_style())
            self.format_button_group.addButton(radio)
            self.format_buttons[key] = radio
            layout.addWidget(radio)

        # Push "More" section to bottom
        layout.addStretch()

        # "More..." dropdown for additional formats
        more_label = QLabel("More:")
        more_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(more_label)

        format_combo = QComboBox()
        format_combo.setMaximumWidth(130)
        format_combo.addItem("Select...", "")

        # Add all formats not in quick options
        quick_keys = {opt[0] for opt in self.FORMAT_QUICK_OPTIONS}
        for key, display_name in sorted(FORMAT_DISPLAY_NAMES.items(), key=lambda x: x[1]):
            if key not in quick_keys and key != "general":  # Skip general (it's in base)
                format_combo.addItem(display_name, key)

        layout.addWidget(format_combo)

        return group, format_combo

    def _create_tone_column(self) -> tuple:
        """Create the TONE column with quick options + dropdown."""
        group = QGroupBox("Tone")
        group.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 12, 6, 6)

        self.tone_button_group = QButtonGroup(self)
        self.tone_buttons: Dict[str, QRadioButton] = {}

        for key, label, tooltip in self.TONE_QUICK_OPTIONS:
            radio = QRadioButton(label)
            radio.setToolTip(tooltip)
            radio.setStyleSheet(self._get_radio_style())
            self.tone_button_group.addButton(radio)
            self.tone_buttons[key] = radio
            layout.addWidget(radio)

        # Push "More" section to bottom
        layout.addStretch()

        # "More..." dropdown for additional tones
        more_label = QLabel("More:")
        more_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(more_label)

        tone_combo = QComboBox()
        tone_combo.setMaximumWidth(130)
        tone_combo.addItem("Select...", "")

        for key, label, tooltip in self.TONE_MORE_OPTIONS:
            tone_combo.addItem(label, key)

        layout.addWidget(tone_combo)

        return group, tone_combo

    def _create_style_column(self) -> Dict[str, QCheckBox]:
        """Create checkbox widgets for STYLE column (multi-select)."""
        checkboxes = {}
        for key, display_name in STYLE_DISPLAY_NAMES.items():
            tooltip = STYLE_TEMPLATES.get(key, "")
            cb = QCheckBox(display_name)
            cb.setToolTip(tooltip)
            cb.setStyleSheet(self._get_checkbox_style())
            checkboxes[key] = cb
        return checkboxes

    def _create_style_container(self) -> QGroupBox:
        """Create the STYLE column container (alphabetically sorted)."""
        group = QGroupBox("Style")
        group.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(6, 12, 6, 6)

        # Sort styles alphabetically
        for key in sorted(self.style_checkboxes.keys()):
            layout.addWidget(self.style_checkboxes[key])

        layout.addStretch()
        return group

    def _get_group_style(self) -> str:
        """Get stylesheet for group boxes."""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 4px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                background-color: #fafafa;
            }
        """

    def _get_radio_style(self) -> str:
        """Get stylesheet for radio buttons."""
        return """
            QRadioButton {
                font-size: 11px;
                padding: 2px 0;
            }
            QRadioButton::indicator {
                width: 12px;
                height: 12px;
            }
        """

    def _get_checkbox_style(self) -> str:
        """Get stylesheet for checkboxes."""
        return """
            QCheckBox {
                font-size: 11px;
                padding: 2px 0;
            }
            QCheckBox::indicator {
                width: 12px;
                height: 12px;
            }
        """

    def _connect_signals(self):
        """Connect all widget signals to emit prompt_changed."""
        # Base column
        self.base_button_group.buttonClicked.connect(self._on_setting_changed)

        # Format column
        self.format_button_group.buttonClicked.connect(self._on_format_radio_changed)
        self.format_combo.currentIndexChanged.connect(self._on_format_combo_changed)

        # Tone column
        self.tone_button_group.buttonClicked.connect(self._on_tone_radio_changed)
        self.tone_combo.currentIndexChanged.connect(self._on_tone_combo_changed)

        # Style checkboxes
        for cb in self.style_checkboxes.values():
            cb.stateChanged.connect(self._on_setting_changed)

        # Reset button
        self.reset_btn.clicked.connect(self._on_reset_clicked)

    def _on_setting_changed(self):
        """Handle any setting change."""
        self._save_to_config()
        self.prompt_changed.emit()

    def _on_format_radio_changed(self):
        """Handle format radio button change - reset combo."""
        self.format_combo.blockSignals(True)
        self.format_combo.setCurrentIndex(0)  # Reset to "Select..."
        self.format_combo.blockSignals(False)
        self._on_setting_changed()

    def _on_format_combo_changed(self, index: int):
        """Handle format combo selection - deselect radio buttons."""
        if index > 0:  # Not "Select..."
            # Deselect all format radio buttons
            checked = self.format_button_group.checkedButton()
            if checked:
                self.format_button_group.setExclusive(False)
                checked.setChecked(False)
                self.format_button_group.setExclusive(True)
            self._on_setting_changed()

    def _on_tone_radio_changed(self):
        """Handle tone radio button change - reset combo."""
        self.tone_combo.blockSignals(True)
        self.tone_combo.setCurrentIndex(0)  # Reset to "Select..."
        self.tone_combo.blockSignals(False)
        self._on_setting_changed()

    def _on_tone_combo_changed(self, index: int):
        """Handle tone combo selection - deselect radio buttons."""
        if index > 0:  # Not "Select..."
            # Deselect all tone radio buttons
            checked = self.tone_button_group.checkedButton()
            if checked:
                self.tone_button_group.setExclusive(False)
                checked.setChecked(False)
                self.tone_button_group.setExclusive(True)
            self._on_setting_changed()

    def _load_from_config(self):
        """Load current settings from config."""
        # Block signals during load
        self._block_all_signals(True)

        # Base selection
        base_preset = self.config.format_preset
        if base_preset == "verbatim":
            self.base_buttons["verbatim"].setChecked(True)
        else:
            self.base_buttons["general"].setChecked(True)

        # Format selection
        format_preset = self.config.format_preset
        if format_preset in self.format_buttons:
            self.format_buttons[format_preset].setChecked(True)
        elif format_preset not in ["general", "verbatim"]:
            # Find in combo
            for i in range(self.format_combo.count()):
                if self.format_combo.itemData(i) == format_preset:
                    self.format_combo.setCurrentIndex(i)
                    break

        # Tone selection
        tone = self.config.formality_level
        if tone in self.tone_buttons:
            self.tone_buttons[tone].setChecked(True)
            self.tone_combo.setCurrentIndex(0)  # Reset combo
        else:
            # Deselect radio buttons and find in combo
            checked = self.tone_button_group.checkedButton()
            if checked:
                self.tone_button_group.setExclusive(False)
                checked.setChecked(False)
                self.tone_button_group.setExclusive(True)
            for i in range(self.tone_combo.count()):
                if self.tone_combo.itemData(i) == tone:
                    self.tone_combo.setCurrentIndex(i)
                    break

        # Style checkboxes
        selected_styles = getattr(self.config, 'selected_styles', [])
        for key, cb in self.style_checkboxes.items():
            cb.setChecked(key in selected_styles)

        self._block_all_signals(False)

    def _save_to_config(self):
        """Save current settings to config."""
        # Determine format preset
        if self.base_buttons["verbatim"].isChecked():
            self.config.format_preset = "verbatim"
        else:
            # Check format radios first
            for key, radio in self.format_buttons.items():
                if radio.isChecked():
                    self.config.format_preset = key if key != "none" else "general"
                    break
            else:
                # Check combo
                combo_key = self.format_combo.currentData()
                if combo_key:
                    self.config.format_preset = combo_key
                else:
                    self.config.format_preset = "general"

        # Tone - check radios first, then combo
        tone_set = False
        for key, radio in self.tone_buttons.items():
            if radio.isChecked():
                self.config.formality_level = key
                tone_set = True
                break

        if not tone_set:
            # Check combo
            combo_key = self.tone_combo.currentData()
            if combo_key:
                self.config.formality_level = combo_key
            else:
                self.config.formality_level = "neutral"

        # Styles (multi-select)
        selected_styles = []
        for key, cb in self.style_checkboxes.items():
            if cb.isChecked():
                selected_styles.append(key)
        self.config.selected_styles = selected_styles

    def _block_all_signals(self, block: bool):
        """Block or unblock all widget signals."""
        self.base_button_group.blockSignals(block)
        self.format_button_group.blockSignals(block)
        self.format_combo.blockSignals(block)
        self.tone_button_group.blockSignals(block)
        self.tone_combo.blockSignals(block)
        for cb in self.style_checkboxes.values():
            cb.blockSignals(block)

    def _on_reset_clicked(self):
        """Reset stack to General with no modifiers."""
        self._block_all_signals(True)

        # Reset to General
        self.base_buttons["general"].setChecked(True)

        # Reset format to None
        self.format_buttons["none"].setChecked(True)
        self.format_combo.setCurrentIndex(0)  # "Select..."

        # Reset tone to Neutral
        self.tone_buttons["neutral"].setChecked(True)
        self.tone_combo.setCurrentIndex(0)  # "Select..."

        # Clear all style checkboxes
        for cb in self.style_checkboxes.values():
            cb.setChecked(False)

        self._block_all_signals(False)

        # Save and emit change
        self._save_to_config()
        self.prompt_changed.emit()

    def get_selected_format(self) -> str:
        """Get the currently selected format preset."""
        return self.config.format_preset

    def refresh(self):
        """Reload settings from config (e.g., after external change)."""
        self._load_from_config()
