"""Prompt Stack Builder Widget

A visual interface for building prompt stacks on the Record tab.
Uses collapsible accordion sections for Format, Tone, and Style.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QRadioButton, QCheckBox, QButtonGroup, QLabel,
    QFrame, QComboBox, QPushButton, QScrollArea,
    QSizePolicy, QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict

try:
    from .config import (
        Config, TONE_TEMPLATES, TONE_DISPLAY_NAMES,
        STYLE_TEMPLATES, STYLE_DISPLAY_NAMES,
        FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES,
    )
    from .tts_announcer import get_announcer
    from .prompt_library import PromptLibrary
except ImportError:
    from config import (
        Config, TONE_TEMPLATES, TONE_DISPLAY_NAMES,
        STYLE_TEMPLATES, STYLE_DISPLAY_NAMES,
        FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES,
    )
    from tts_announcer import get_announcer
    from prompt_library import PromptLibrary


class CollapsibleSection(QWidget):
    """A collapsible accordion section with header and content."""

    toggled = pyqtSignal(bool)  # Emitted when expanded/collapsed

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._expanded = False
        self._summary = ""

        self._setup_ui()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header (clickable)
        self.header = QFrame()
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.setStyleSheet("""
            QFrame {
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QFrame:hover {
                background-color: #dee2e6;
            }
        """)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(6)

        # Arrow
        self.arrow = QLabel("▶")
        self.arrow.setStyleSheet("font-size: 9px; color: #666;")
        header_layout.addWidget(self.arrow)

        # Title
        self.title_label = QLabel(f"<b>{self._title}</b>")
        self.title_label.setStyleSheet("font-size: 11px; color: #333;")
        header_layout.addWidget(self.title_label)

        # Summary (shows current selection)
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-size: 11px; color: #666;")
        header_layout.addWidget(self.summary_label)

        header_layout.addStretch()

        self.header.mousePressEvent = self._on_header_click
        layout.addWidget(self.header)

        # Content container
        self.content = QWidget()
        self.content.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-top: none;
                border-radius: 0 0 4px 4px;
            }
        """)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 8, 10, 8)
        self.content_layout.setSpacing(4)
        self.content.setVisible(False)
        layout.addWidget(self.content)

    def _on_header_click(self, event):
        self.set_expanded(not self._expanded)

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self.arrow.setText("▼" if expanded else "▶")
        self.content.setVisible(expanded)
        # Update header style when expanded
        if expanded:
            self.header.setStyleSheet("""
                QFrame {
                    background-color: #dee2e6;
                    border: 1px solid #dee2e6;
                    border-radius: 4px 4px 0 0;
                }
                QFrame:hover {
                    background-color: #ced4da;
                }
            """)
        else:
            self.header.setStyleSheet("""
                QFrame {
                    background-color: #e9ecef;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                }
                QFrame:hover {
                    background-color: #dee2e6;
                }
            """)
        self.toggled.emit(expanded)
        # Force size recalculation
        self.adjustSize()

    def is_expanded(self) -> bool:
        return self._expanded

    def set_summary(self, text: str):
        self._summary = text
        if text:
            self.summary_label.setText(f"— {text}")
        else:
            self.summary_label.setText("")

    def add_widget(self, widget: QWidget):
        self.content_layout.addWidget(widget)


class StackBuilderWidget(QWidget):
    """Visual prompt stack builder with collapsible accordions.

    Provides a compact interface for building prompt layers:
    - BASE: General vs Verbatim (always visible, mutually exclusive)
    - FORMAT: Output format presets (collapsible, mutually exclusive)
    - TONE: Formality level (collapsible, mutually exclusive)
    - STYLE: Writing styles (collapsible, multi-select)

    Emits prompt_changed signal when any selection changes.
    """

    prompt_changed = pyqtSignal()

    # Base options (mutually exclusive)
    BASE_OPTIONS = [
        ("general", "General", "Standard cleanup and formatting"),
        ("verbatim", "Verbatim", "Minimal transformation, close to original speech"),
    ]

    # Format options
    FORMAT_QUICK_OPTIONS = [
        ("none", "None", "No specific format - general cleanup only"),
        ("ai_prompt", "AI Prompt", "Format as an AI prompt"),
        ("email", "Email", "Format as an email with greeting and signature"),
        ("meeting_agenda", "Agenda", "Format as a meeting agenda"),
        ("meeting_minutes", "Minutes", "Format as formal meeting minutes"),
        ("social_post", "Social Post", "Format for social media/community"),
        ("todo", "To-Do", "Format as a to-do list"),
    ]

    # Tone options (mutually exclusive)
    TONE_QUICK_OPTIONS = [
        ("neutral", "Neutral", "No specific tone modifier"),
        ("casual", "Casual", "Relaxed, conversational tone"),
        ("professional", "Professional", "Formal business tone"),
        ("friendly", "Friendly", "Warm, approachable tone"),
    ]

    TONE_MORE_OPTIONS = [
        ("authoritative", "Authoritative", "Confident, expert tone"),
        ("enthusiastic", "Enthusiastic", "Energetic, excited tone"),
        ("empathetic", "Empathetic", "Understanding, caring tone"),
        ("urgent", "Urgent", "Time-sensitive, pressing tone"),
        ("reassuring", "Reassuring", "Calm, comforting tone"),
    ]

    def __init__(self, config: Config, config_dir=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.config_dir = config_dir
        self._was_verbatim = config.format_preset == "verbatim"

        # Load prompt library for custom prompts
        self.library = PromptLibrary(config_dir) if config_dir else None

        self._setup_ui()
        self._load_from_config()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the UI with collapsible accordion sections."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Main container with unified background
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(8)

        # Top row: Infer Format + Base options + Reset
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        # Infer Format checkbox
        self.infer_format_checkbox = QCheckBox("Infer Format")
        self.infer_format_checkbox.setToolTip(
            "Let the AI infer the intended format from the content"
        )
        self.infer_format_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #444;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
        """)
        top_row.addWidget(self.infer_format_checkbox)

        # Base options (always visible)
        base_frame = QFrame()
        base_frame.setStyleSheet("QFrame { border: none; background: transparent; }")
        base_layout = QHBoxLayout(base_frame)
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_layout.setSpacing(12)

        self.base_button_group = QButtonGroup(self)
        self.base_buttons: Dict[str, QRadioButton] = {}

        for key, label, tooltip in self.BASE_OPTIONS:
            radio = QRadioButton(label)
            radio.setToolTip(tooltip)
            radio.setStyleSheet("""
                QRadioButton {
                    font-size: 11px;
                    font-weight: bold;
                }
                QRadioButton::indicator {
                    width: 14px;
                    height: 14px;
                }
            """)
            self.base_button_group.addButton(radio)
            self.base_buttons[key] = radio
            base_layout.addWidget(radio)

        top_row.addWidget(base_frame)
        top_row.addStretch()

        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setToolTip("Reset to General with no modifiers")
        self.reset_btn.setMaximumWidth(60)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                color: #666;
            }
            QPushButton:hover {
                background-color: #dee2e6;
                border-color: #adb5bd;
            }
        """)
        top_row.addWidget(self.reset_btn)

        container_layout.addLayout(top_row)

        # Accordion sections row
        accordions_layout = QHBoxLayout()
        accordions_layout.setSpacing(8)
        accordions_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # FORMAT section
        self.format_section = CollapsibleSection("Format")
        self.format_section.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._setup_format_section()
        accordions_layout.addWidget(self.format_section, 0, Qt.AlignmentFlag.AlignTop)

        # TONE section
        self.tone_section = CollapsibleSection("Tone")
        self.tone_section.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._setup_tone_section()
        accordions_layout.addWidget(self.tone_section, 0, Qt.AlignmentFlag.AlignTop)

        # STYLE section
        self.style_section = CollapsibleSection("Style")
        self.style_section.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._setup_style_section()
        accordions_layout.addWidget(self.style_section, 0, Qt.AlignmentFlag.AlignTop)

        accordions_layout.addStretch()
        container_layout.addLayout(accordions_layout)

        main_layout.addWidget(container)

    def _setup_format_section(self):
        """Set up the format accordion content."""
        self.format_button_group = QButtonGroup(self)
        self.format_buttons: Dict[str, QRadioButton] = {}

        for key, label, tooltip in self.FORMAT_QUICK_OPTIONS:
            radio = QRadioButton(label)
            radio.setToolTip(tooltip)
            radio.setStyleSheet(self._get_radio_style())
            self.format_button_group.addButton(radio)
            self.format_buttons[key] = radio
            self.format_section.add_widget(radio)

        # More dropdown
        more_container = QWidget()
        more_container.setStyleSheet("background: transparent; border: none;")
        more_layout = QHBoxLayout(more_container)
        more_layout.setContentsMargins(0, 4, 0, 0)
        more_layout.setSpacing(4)

        more_label = QLabel("More:")
        more_label.setStyleSheet("color: #666; font-size: 10px; border: none;")
        more_layout.addWidget(more_label)

        self.format_combo = QComboBox()
        self.format_combo.setMaximumWidth(140)
        self.format_combo.addItem("Select...", "")

        quick_keys = {opt[0] for opt in self.FORMAT_QUICK_OPTIONS}
        for key, display_name in sorted(FORMAT_DISPLAY_NAMES.items(), key=lambda x: x[1]):
            if key not in quick_keys and key != "general":
                self.format_combo.addItem(display_name, key)

        # Add custom format prompts
        custom_formats = self._get_custom_prompts("format")
        if custom_formats:
            self.format_combo.insertSeparator(self.format_combo.count())
            for prompt in custom_formats:
                self.format_combo.addItem(f"✦ {prompt.name}", f"custom:{prompt.id}")

        more_layout.addWidget(self.format_combo)
        more_layout.addStretch()
        self.format_section.add_widget(more_container)

    def _setup_tone_section(self):
        """Set up the tone accordion content."""
        self.tone_button_group = QButtonGroup(self)
        self.tone_buttons: Dict[str, QRadioButton] = {}

        for key, label, tooltip in self.TONE_QUICK_OPTIONS:
            radio = QRadioButton(label)
            radio.setToolTip(tooltip)
            radio.setStyleSheet(self._get_radio_style())
            self.tone_button_group.addButton(radio)
            self.tone_buttons[key] = radio
            self.tone_section.add_widget(radio)

        # More dropdown
        more_container = QWidget()
        more_container.setStyleSheet("background: transparent; border: none;")
        more_layout = QHBoxLayout(more_container)
        more_layout.setContentsMargins(0, 4, 0, 0)
        more_layout.setSpacing(4)

        more_label = QLabel("More:")
        more_label.setStyleSheet("color: #666; font-size: 10px; border: none;")
        more_layout.addWidget(more_label)

        self.tone_combo = QComboBox()
        self.tone_combo.setMaximumWidth(140)
        self.tone_combo.addItem("Select...", "")

        for key, label, tooltip in self.TONE_MORE_OPTIONS:
            self.tone_combo.addItem(label, key)

        # Add custom tone prompts
        custom_tones = self._get_custom_prompts("tone")
        if custom_tones:
            self.tone_combo.insertSeparator(self.tone_combo.count())
            for prompt in custom_tones:
                self.tone_combo.addItem(f"✦ {prompt.name}", f"custom:{prompt.id}")

        more_layout.addWidget(self.tone_combo)
        more_layout.addStretch()
        self.tone_section.add_widget(more_container)

    def _setup_style_section(self):
        """Set up the style accordion content (multi-select checkboxes)."""
        self.style_checkboxes: Dict[str, QCheckBox] = {}

        # Create a grid layout for styles (2 columns)
        grid_container = QWidget()
        grid_container.setStyleSheet("background: transparent; border: none;")
        grid = QGridLayout(grid_container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)

        # Add builtin styles
        sorted_styles = sorted(STYLE_DISPLAY_NAMES.items(), key=lambda x: x[1])
        for i, (key, display_name) in enumerate(sorted_styles):
            tooltip = STYLE_TEMPLATES.get(key, "")
            cb = QCheckBox(display_name)
            cb.setToolTip(tooltip)
            cb.setStyleSheet(self._get_checkbox_style())
            self.style_checkboxes[key] = cb
            row = i // 2
            col = i % 2
            grid.addWidget(cb, row, col)

        # Add custom style prompts
        custom_styles = self._get_custom_prompts("style")
        if custom_styles:
            start_row = (len(sorted_styles) + 1) // 2
            for i, prompt in enumerate(custom_styles):
                cb = QCheckBox(f"✦ {prompt.name}")
                cb.setToolTip(prompt.instruction[:100] + "..." if len(prompt.instruction) > 100 else prompt.instruction)
                cb.setStyleSheet(self._get_checkbox_style())
                self.style_checkboxes[f"custom:{prompt.id}"] = cb
                row = start_row + (i // 2)
                col = i % 2
                grid.addWidget(cb, row, col)

        self.style_section.add_widget(grid_container)

    def _get_radio_style(self) -> str:
        return """
            QRadioButton {
                font-size: 11px;
                padding: 2px 0;
                background: transparent;
                border: none;
            }
            QRadioButton::indicator {
                width: 12px;
                height: 12px;
            }
        """

    def _get_checkbox_style(self) -> str:
        return """
            QCheckBox {
                font-size: 11px;
                padding: 2px 0;
                background: transparent;
                border: none;
            }
            QCheckBox::indicator {
                width: 12px;
                height: 12px;
            }
        """

    def _get_custom_prompts(self, prompt_type: str) -> list:
        """Get custom prompts of a specific type from the library."""
        if not self.library:
            return []
        return self.library.get_custom_by_type(prompt_type)

    def refresh_custom_prompts(self):
        """Refresh the UI to show newly added custom prompts.

        Call this after custom prompts are added/edited/deleted in the Prompt Manager.
        """
        if self.library:
            self.library._load_custom()  # Reload from disk

        # Rebuild the sections to include new custom prompts
        # This is a simplified refresh - in production you might want to
        # selectively update only the changed sections
        self._setup_ui()
        self._load_from_config()
        self._connect_signals()

    def _connect_signals(self):
        """Connect all widget signals."""
        self.infer_format_checkbox.stateChanged.connect(self._on_infer_format_changed)
        self.base_button_group.buttonClicked.connect(self._on_base_changed)
        self.format_button_group.buttonClicked.connect(self._on_format_radio_changed)
        self.format_combo.currentIndexChanged.connect(self._on_format_combo_changed)
        self.tone_button_group.buttonClicked.connect(self._on_tone_radio_changed)
        self.tone_combo.currentIndexChanged.connect(self._on_tone_combo_changed)

        for cb in self.style_checkboxes.values():
            cb.stateChanged.connect(self._on_style_changed)

        self.reset_btn.clicked.connect(self._on_reset_clicked)

    def _is_tts_enabled(self) -> bool:
        return getattr(self.config, 'audio_feedback_mode', 'beeps') == 'tts'

    def _announce_tts(self, announcement_type: str):
        if not self._is_tts_enabled():
            return

        announcer = get_announcer()
        if announcement_type == 'format':
            announcer.announce_format_updated()
        elif announcement_type == 'tone':
            announcer.announce_tone_updated()
        elif announcement_type == 'style':
            announcer.announce_style_updated()
        elif announcement_type == 'verbatim':
            announcer.announce_verbatim_mode()
        elif announcement_type == 'general':
            announcer.announce_general_mode()
        elif announcement_type == 'format_inference':
            announcer.announce_format_inference()
        elif announcement_type == 'default_prompt_configured':
            announcer.announce_default_prompt_configured()

    def _on_infer_format_changed(self, state: int):
        is_checked = (state == Qt.CheckState.Checked.value)
        self.config.prompt_infer_format = is_checked
        if is_checked:
            self._announce_tts('format_inference')
        self.prompt_changed.emit()

    def _on_setting_changed(self):
        self._save_to_config()
        self._update_summaries()
        self.prompt_changed.emit()

    def _on_base_changed(self):
        is_now_verbatim = self.base_buttons["verbatim"].isChecked()

        if is_now_verbatim and not self._was_verbatim:
            self._announce_tts('verbatim')
        elif not is_now_verbatim and self._was_verbatim:
            self._announce_tts('general')

        self._was_verbatim = is_now_verbatim
        self._on_setting_changed()

    def _on_style_changed(self, state: int):
        self._announce_tts('style')
        self._on_setting_changed()

    def _on_format_radio_changed(self):
        self.format_combo.blockSignals(True)
        self.format_combo.setCurrentIndex(0)
        self.format_combo.blockSignals(False)
        self._announce_tts('format')
        self._on_setting_changed()

    def _on_format_combo_changed(self, index: int):
        if index > 0:
            checked = self.format_button_group.checkedButton()
            if checked:
                self.format_button_group.setExclusive(False)
                checked.setChecked(False)
                self.format_button_group.setExclusive(True)
            self._announce_tts('format')
            self._on_setting_changed()

    def _on_tone_radio_changed(self):
        self.tone_combo.blockSignals(True)
        self.tone_combo.setCurrentIndex(0)
        self.tone_combo.blockSignals(False)
        self._announce_tts('tone')
        self._on_setting_changed()

    def _on_tone_combo_changed(self, index: int):
        if index > 0:
            checked = self.tone_button_group.checkedButton()
            if checked:
                self.tone_button_group.setExclusive(False)
                checked.setChecked(False)
                self.tone_button_group.setExclusive(True)
            self._announce_tts('tone')
            self._on_setting_changed()

    def _load_from_config(self):
        """Load current settings from config."""
        self._block_all_signals(True)

        self.infer_format_checkbox.setChecked(
            getattr(self.config, 'prompt_infer_format', True)
        )

        base_preset = self.config.format_preset
        if base_preset == "verbatim":
            self.base_buttons["verbatim"].setChecked(True)
        else:
            self.base_buttons["general"].setChecked(True)

        format_preset = self.config.format_preset
        if format_preset in self.format_buttons:
            self.format_buttons[format_preset].setChecked(True)
        elif format_preset not in ["general", "verbatim"]:
            for i in range(self.format_combo.count()):
                if self.format_combo.itemData(i) == format_preset:
                    self.format_combo.setCurrentIndex(i)
                    break

        tone = self.config.formality_level
        if tone in self.tone_buttons:
            self.tone_buttons[tone].setChecked(True)
            self.tone_combo.setCurrentIndex(0)
        else:
            checked = self.tone_button_group.checkedButton()
            if checked:
                self.tone_button_group.setExclusive(False)
                checked.setChecked(False)
                self.tone_button_group.setExclusive(True)
            for i in range(self.tone_combo.count()):
                if self.tone_combo.itemData(i) == tone:
                    self.tone_combo.setCurrentIndex(i)
                    break

        selected_styles = getattr(self.config, 'selected_styles', [])
        for key, cb in self.style_checkboxes.items():
            cb.setChecked(key in selected_styles)

        self._block_all_signals(False)
        self._update_summaries()

    def _save_to_config(self):
        """Save current settings to config."""
        if self.base_buttons["verbatim"].isChecked():
            self.config.format_preset = "verbatim"
        else:
            for key, radio in self.format_buttons.items():
                if radio.isChecked():
                    self.config.format_preset = key if key != "none" else "general"
                    break
            else:
                combo_key = self.format_combo.currentData()
                if combo_key:
                    self.config.format_preset = combo_key
                else:
                    self.config.format_preset = "general"

        tone_set = False
        for key, radio in self.tone_buttons.items():
            if radio.isChecked():
                self.config.formality_level = key
                tone_set = True
                break

        if not tone_set:
            combo_key = self.tone_combo.currentData()
            if combo_key:
                self.config.formality_level = combo_key
            else:
                self.config.formality_level = "neutral"

        selected_styles = []
        for key, cb in self.style_checkboxes.items():
            if cb.isChecked():
                selected_styles.append(key)
        self.config.selected_styles = selected_styles

    def _block_all_signals(self, block: bool):
        self.infer_format_checkbox.blockSignals(block)
        self.base_button_group.blockSignals(block)
        self.format_button_group.blockSignals(block)
        self.format_combo.blockSignals(block)
        self.tone_button_group.blockSignals(block)
        self.tone_combo.blockSignals(block)
        for cb in self.style_checkboxes.values():
            cb.blockSignals(block)

    def _update_summaries(self):
        """Update accordion header summaries with current selections."""
        # Format summary
        format_text = "None"
        for key, radio in self.format_buttons.items():
            if radio.isChecked() and key != "none":
                for k, label, _ in self.FORMAT_QUICK_OPTIONS:
                    if k == key:
                        format_text = label
                        break
                break
        else:
            combo_key = self.format_combo.currentData()
            if combo_key:
                format_text = FORMAT_DISPLAY_NAMES.get(combo_key, combo_key)

        self.format_section.set_summary(format_text if format_text != "None" else "")

        # Tone summary
        tone_text = "Neutral"
        for key, radio in self.tone_buttons.items():
            if radio.isChecked() and key != "neutral":
                for k, label, _ in self.TONE_QUICK_OPTIONS:
                    if k == key:
                        tone_text = label
                        break
                break
        else:
            combo_key = self.tone_combo.currentData()
            if combo_key:
                for k, label, _ in self.TONE_MORE_OPTIONS:
                    if k == combo_key:
                        tone_text = label
                        break

        self.tone_section.set_summary(tone_text if tone_text != "Neutral" else "")

        # Style summary
        style_count = sum(1 for cb in self.style_checkboxes.values() if cb.isChecked())
        if style_count > 0:
            self.style_section.set_summary(f"{style_count} selected")
        else:
            self.style_section.set_summary("")

    def _on_reset_clicked(self):
        """Reset stack to General with no modifiers."""
        self._block_all_signals(True)

        self.infer_format_checkbox.setChecked(False)
        self.config.prompt_infer_format = False

        self.base_buttons["general"].setChecked(True)
        self.format_buttons["none"].setChecked(True)
        self.format_combo.setCurrentIndex(0)
        self.tone_buttons["neutral"].setChecked(True)
        self.tone_combo.setCurrentIndex(0)

        for cb in self.style_checkboxes.values():
            cb.setChecked(False)

        self._block_all_signals(False)

        self._save_to_config()
        self._update_summaries()
        self._announce_tts('default_prompt_configured')
        self.prompt_changed.emit()

    def get_selected_format(self) -> str:
        return self.config.format_preset

    def refresh(self):
        """Reload settings from config."""
        self._load_from_config()

    # Legacy compatibility methods
    def is_collapsed(self) -> bool:
        return False

    def set_collapsed(self, collapsed: bool, animate: bool = True):
        pass
