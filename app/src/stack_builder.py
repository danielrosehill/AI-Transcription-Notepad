"""Prompt Stack Builder Widget

A visual interface for building prompt stacks on the Record tab.
Uses collapsible accordion sections for Format, Tone, Style, and Stacks.
Each section has quick-access toggle buttons plus a searchable dropdown.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QRadioButton, QCheckBox, QButtonGroup, QLabel,
    QFrame, QComboBox, QPushButton, QScrollArea,
    QSizePolicy, QGridLayout, QCompleter,
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, List
from pathlib import Path

try:
    from .config import (
        Config, TONE_TEMPLATES, TONE_DISPLAY_NAMES,
        STYLE_TEMPLATES, STYLE_DISPLAY_NAMES,
        FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES, FORMAT_ICONS,
        TRANSLATION_LANGUAGES, get_language_display_name, get_language_flag,
    )
    from .tts_announcer import get_announcer
    from .prompt_library import PromptLibrary
    from .prompt_elements import get_all_stacks, PromptStack, ALL_ELEMENTS
except ImportError:
    from config import (
        Config, TONE_TEMPLATES, TONE_DISPLAY_NAMES,
        STYLE_TEMPLATES, STYLE_DISPLAY_NAMES,
        FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES, FORMAT_ICONS,
        TRANSLATION_LANGUAGES, get_language_display_name, get_language_flag,
    )
    from tts_announcer import get_announcer
    from prompt_library import PromptLibrary
    from prompt_elements import get_all_stacks, PromptStack, ALL_ELEMENTS


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
                background-color: #f8f9fa;
                border: none;
                border-radius: 4px;
            }
            QFrame:hover {
                background-color: #e9ecef;
            }
        """)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(6)

        # Arrow
        self.arrow = QLabel("▶")
        self.arrow.setStyleSheet("font-size: 10px; color: #666;")
        header_layout.addWidget(self.arrow)

        # Title
        self.title_label = QLabel(f"<b>{self._title}</b>")
        self.title_label.setStyleSheet("font-size: 12px; color: #333;")
        header_layout.addWidget(self.title_label)

        # Summary (shows current selection)
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-size: 12px; color: #666;")
        header_layout.addWidget(self.summary_label)

        header_layout.addStretch()

        self.header.mousePressEvent = self._on_header_click
        layout.addWidget(self.header)

        # Content container
        self.content = QWidget()
        self.content.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: none;
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
                    background-color: #e9ecef;
                    border: none;
                    border-radius: 4px 4px 0 0;
                }
                QFrame:hover {
                    background-color: #dee2e6;
                }
            """)
        else:
            self.header.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: none;
                    border-radius: 4px;
                }
                QFrame:hover {
                    background-color: #e9ecef;
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
        ("translation", "Translation", "Transcribe and translate to target language"),
    ]

    # Format options (9 common formats, 3 rows of 3 alphabetically)
    FORMAT_QUICK_OPTIONS = [
        # Row 1
        ("meeting_agenda", f"{FORMAT_ICONS.get('meeting_agenda', '')} Agenda", "Format as a meeting agenda"),
        ("ai_prompt", f"{FORMAT_ICONS.get('ai_prompt', '')} AI Prompt", "Format as an AI prompt"),
        ("blog_outline", f"{FORMAT_ICONS.get('blog_outline', '')} Blog Outline", "Format as a blog post outline"),
        # Row 2
        ("dev_prompt", f"{FORMAT_ICONS.get('dev_prompt', '')} Dev Prompt", "Format as development instructions for AI"),
        ("email", f"{FORMAT_ICONS.get('email', '')} Email", "Format as an email with greeting and signature"),
        ("meeting_minutes", f"{FORMAT_ICONS.get('meeting_minutes', '')} Minutes", "Format as formal meeting minutes"),
        # Row 3
        ("meeting_notes", f"{FORMAT_ICONS.get('meeting_notes', '')} Notes", "Format as structured meeting notes"),
        ("social_post", f"{FORMAT_ICONS.get('social_post', '')} Social Post", "Format for social media/community"),
        ("todo", f"{FORMAT_ICONS.get('todo', '')} To-Do", "Format as a to-do list"),
    ]

    # Tone options (quick-access, mutually exclusive)
    TONE_OPTIONS = [
        ("default", "Default", "No tone direction — uses natural tone"),
        ("casual", "Casual", "Relaxed, conversational tone"),
        ("professional", "Professional", "Formal business tone"),
    ]

    def __init__(self, config: Config, config_dir=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.config_dir = config_dir
        self._was_verbatim = config.format_preset == "verbatim"
        self._was_translation = config.translation_mode_enabled

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
                background-color: transparent;
                border: none;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)

        # Top row: Base options + Reset
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

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
                    font-size: 13px;
                    font-weight: bold;
                    padding: 4px 2px;
                    spacing: 6px;
                    color: #333;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
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

        # FORMAT section (always visible, not in accordion)
        format_heading = QLabel("Format")
        format_heading.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #666;
                padding: 6px 0 4px 0;
            }
        """)
        format_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(format_heading)

        self._setup_format_section(container_layout)

        # TONE section (exposed like format, not in accordion)
        tone_heading = QLabel("Tone")
        tone_heading.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #666;
                padding: 6px 0 4px 0;
            }
        """)
        tone_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(tone_heading)

        self._setup_tone_section(container_layout)

        # "Customize Output" heading for accordion sections
        heading_label = QLabel("Customize Output")
        heading_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #666;
                padding: 6px 0 4px 0;
            }
        """)
        heading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(heading_label)

        # Accordion sections row - center-aligned (Style, Stacks only)
        accordions_layout = QHBoxLayout()
        accordions_layout.setSpacing(8)
        accordions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)

        # STYLE section
        self.style_section = CollapsibleSection("Style")
        self.style_section.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._setup_style_section()
        accordions_layout.addWidget(self.style_section, 0, Qt.AlignmentFlag.AlignTop)

        # STACKS section
        self.stacks_section = CollapsibleSection("Stacks")
        self.stacks_section.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._setup_stacks_section()
        accordions_layout.addWidget(self.stacks_section, 0, Qt.AlignmentFlag.AlignTop)

        container_layout.addLayout(accordions_layout)

        main_layout.addWidget(container)

    def _setup_format_section(self, parent_layout):
        """Set up the format checkboxes in 3 rows of 3 + searchable dropdown.

        Formats are mutually exclusive - only one can be active at a time.
        Exposed directly (not in an accordion) since these are frequently used.
        """
        self.format_checkboxes: Dict[str, QCheckBox] = {}
        self._format_from_more = None  # Track format selected from More dropdown

        # Create a grid layout for formats (3 rows of 3)
        grid_container = QWidget()
        grid_container.setStyleSheet("background: transparent; border: none;")
        grid = QGridLayout(grid_container)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(6)

        for i, (key, label, tooltip) in enumerate(self.FORMAT_QUICK_OPTIONS):
            cb = QCheckBox(label)
            cb.setToolTip(tooltip)
            cb.setStyleSheet(self._get_checkbox_style())
            cb.stateChanged.connect(lambda state, k=key: self._on_format_checkbox_changed(k, state))
            self.format_checkboxes[key] = cb
            row = i // 3
            col = i % 3
            grid.addWidget(cb, row, col)

        parent_layout.addWidget(grid_container)

        # Searchable dropdown for additional formats
        more_container = QWidget()
        more_container.setStyleSheet("background: transparent; border: none;")
        more_layout = QHBoxLayout(more_container)
        more_layout.setContentsMargins(0, 0, 0, 0)
        more_layout.setSpacing(4)

        more_label = QLabel("Type a format:")
        more_label.setStyleSheet("color: #666; font-size: 12px; border: none;")
        more_layout.addWidget(more_label)

        self.format_combo = self._create_searchable_combo("Search formats...")
        self.format_combo.setMaximumWidth(200)
        self.format_combo.addItem("Select...", "")

        # Add formats not in quick options
        quick_keys = {opt[0] for opt in self.FORMAT_QUICK_OPTIONS}
        for key, display_name in sorted(FORMAT_DISPLAY_NAMES.items(), key=lambda x: x[1]):
            if key not in quick_keys and key != "general":
                icon = FORMAT_ICONS.get(key, "")
                label = f"{icon} {display_name}" if icon else display_name
                self.format_combo.addItem(label, key)

        # Add custom format prompts
        custom_formats = self._get_custom_prompts("format")
        if custom_formats:
            self.format_combo.insertSeparator(self.format_combo.count())
            for prompt in custom_formats:
                self.format_combo.addItem(f"✦ {prompt.name}", f"custom:{prompt.id}")

        self._setup_combo_completer(self.format_combo)
        more_layout.addWidget(self.format_combo)
        more_layout.addStretch()
        parent_layout.addWidget(more_container)

    def _setup_tone_section(self, parent_layout):
        """Set up the tone radio buttons (mutually exclusive: Default, Casual, Professional)."""
        self.tone_button_group = QButtonGroup(self)
        self.tone_buttons: Dict[str, QRadioButton] = {}

        tone_container = QWidget()
        tone_container.setStyleSheet("background: transparent; border: none;")
        tone_layout = QHBoxLayout(tone_container)
        tone_layout.setContentsMargins(0, 0, 0, 0)
        tone_layout.setSpacing(16)
        tone_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for key, label, tooltip in self.TONE_OPTIONS:
            radio = QRadioButton(label)
            radio.setToolTip(tooltip)
            radio.setStyleSheet("""
                QRadioButton {
                    font-size: 13px;
                    padding: 4px 6px;
                    background: transparent;
                    border: none;
                    spacing: 6px;
                    color: #333;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                }
            """)
            self.tone_button_group.addButton(radio)
            self.tone_buttons[key] = radio
            tone_layout.addWidget(radio)

        # Default is selected by default
        self.tone_buttons["default"].setChecked(True)

        parent_layout.addWidget(tone_container)

    def _setup_style_section(self):
        """Set up the style accordion content with checkboxes (multi-select)."""
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
            cb.stateChanged.connect(self._on_style_checkbox_changed)
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
                cb.stateChanged.connect(self._on_style_checkbox_changed)
                self.style_checkboxes[f"custom:{prompt.id}"] = cb
                row = start_row + (i // 2)
                col = i % 2
                grid.addWidget(cb, row, col)

        self.style_section.add_widget(grid_container)

    def _setup_stacks_section(self):
        """Set up the stacks accordion content with searchable dropdown."""
        # Searchable stacks dropdown
        self.stacks_combo = self._create_searchable_combo("Search stacks...")

        # Add "None" option first
        self.stacks_combo.addItem("None (use individual settings)", "")

        # Get all stacks (default + custom)
        all_stacks = get_all_stacks(Path(self.config_dir)) if self.config_dir else []

        # Sort stacks alphabetically by name
        all_stacks = sorted(all_stacks, key=lambda s: s.name.lower())

        for stack in all_stacks:
            # Format: "Name — description"
            display_text = stack.name
            if stack.description:
                display_text = f"{stack.name} — {stack.description}"
            self.stacks_combo.addItem(display_text, stack.name)

        # Set up completer for search
        self._setup_combo_completer(self.stacks_combo)

        self.stacks_section.add_widget(self.stacks_combo)

    def _get_radio_style(self) -> str:
        return """
            QRadioButton {
                font-size: 13px;
                padding: 4px 2px;
                background: transparent;
                border: none;
                spacing: 6px;
                color: #333;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """

    def _get_checkbox_style(self) -> str:
        return """
            QCheckBox {
                font-size: 13px;
                padding: 4px 2px;
                background: transparent;
                border: none;
                spacing: 6px;
                color: #333;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """

    def _get_toggle_button_style(self) -> str:
        """Style for toggle buttons that can be checked/unchecked."""
        return """
            QPushButton {
                font-size: 10px;
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f9fa;
                color: #333;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:checked {
                background-color: #0078d4;
                border-color: #0078d4;
                color: white;
            }
            QPushButton:checked:hover {
                background-color: #006cbd;
            }
        """

    def _create_searchable_combo(self, placeholder: str = "Type to search...") -> QComboBox:
        """Create a searchable combo box with autocomplete."""
        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        combo.setMinimumWidth(180)
        combo.setPlaceholderText(placeholder)
        combo.setStyleSheet("""
            QComboBox {
                font-size: 13px;
                padding: 6px 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                font-size: 13px;
            }
        """)
        return combo

    def _setup_combo_completer(self, combo: QComboBox):
        """Set up a completer for case-insensitive substring matching."""
        items = [combo.itemText(i) for i in range(combo.count())]
        completer = QCompleter(items)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        combo.setCompleter(completer)

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
        self.base_button_group.buttonClicked.connect(self._on_base_changed)
        # Format/Style checkboxes are connected in setup methods
        self.format_combo.currentIndexChanged.connect(self._on_format_combo_changed)
        self.tone_button_group.buttonClicked.connect(self._on_tone_changed)
        self.stacks_combo.currentIndexChanged.connect(self._on_stacks_changed)
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
        elif announcement_type == 'translation':
            announcer.announce_translation_mode()
        elif announcement_type == 'format_inference':
            announcer.announce_format_inference()
        elif announcement_type == 'default_prompt_configured':
            announcer.announce_default_prompt_configured()


    def _on_setting_changed(self):
        self._save_to_config()
        self._update_summaries()
        self.prompt_changed.emit()

    def _on_base_changed(self):
        is_now_verbatim = self.base_buttons["verbatim"].isChecked()
        is_now_translation = self.base_buttons["translation"].isChecked()

        # Handle TTS announcements for mode changes
        if is_now_verbatim and not self._was_verbatim:
            self._announce_tts('verbatim')
        elif is_now_translation and not self._was_translation:
            self._announce_tts('translation')
        elif not is_now_verbatim and self._was_verbatim:
            if not is_now_translation:
                self._announce_tts('general')
        elif not is_now_translation and self._was_translation:
            if not is_now_verbatim:
                self._announce_tts('general')

        self._was_verbatim = is_now_verbatim
        self._was_translation = is_now_translation
        self._on_setting_changed()

    def _on_format_checkbox_changed(self, key: str, state: int):
        """Handle format checkbox state change.

        Formats are mutually exclusive - checking one unchecks all others.
        Also clears any selection from the More dropdown.
        """
        if state == 2:  # Checked
            # Uncheck all other format checkboxes
            self._block_format_signals(True)
            for other_key, cb in self.format_checkboxes.items():
                if other_key != key:
                    cb.setChecked(False)
            self._block_format_signals(False)
            # Clear any More dropdown selection
            self._format_from_more = None
            self.format_combo.blockSignals(True)
            self.format_combo.setCurrentIndex(0)
            self.format_combo.blockSignals(False)
        self._announce_tts('format')
        self._on_setting_changed()

    def _on_format_combo_changed(self, index: int):
        """Handle format dropdown selection change.

        Selecting from More clears all checkbox selections and sets
        the format to the single dropdown selection.
        """
        if index > 0:  # Not "Select..."
            format_key = self.format_combo.currentData()
            # Clear all format checkboxes
            self._block_format_signals(True)
            for cb in self.format_checkboxes.values():
                cb.setChecked(False)
            self._block_format_signals(False)
            # Track the More selection
            self._format_from_more = format_key
            self._announce_tts('format')
            self._on_setting_changed()

    def _block_format_signals(self, block: bool):
        """Block or unblock signals from format checkboxes only."""
        for cb in self.format_checkboxes.values():
            cb.blockSignals(block)

    def _on_tone_changed(self):
        """Handle tone radio button change."""
        self._announce_tts('tone')
        self._on_setting_changed()

    def _on_style_checkbox_changed(self, state: int):
        """Handle style checkbox state change."""
        self._announce_tts('style')
        self._on_setting_changed()

    def _on_stacks_changed(self, index: int):
        """Handle stacks dropdown selection change."""
        stack_name = self.stacks_combo.currentData()
        if stack_name:
            # Find and apply the selected stack
            all_stacks = get_all_stacks(Path(self.config_dir)) if self.config_dir else []
            for stack in all_stacks:
                if stack.name == stack_name:
                    self.apply_stack(stack)
                    break
        self._on_setting_changed()

    def _load_from_config(self):
        """Load current settings from config."""
        self._block_all_signals(True)


        # Base preset (General vs Verbatim vs Translation)
        base_preset = self.config.format_preset
        translation_enabled = getattr(self.config, 'translation_mode_enabled', False)

        if translation_enabled:
            self.base_buttons["translation"].setChecked(True)
        elif base_preset == "verbatim":
            self.base_buttons["verbatim"].setChecked(True)
        else:
            self.base_buttons["general"].setChecked(True)

        # Format selection (mutually exclusive)
        selected_formats = getattr(self.config, 'selected_formats', [])
        # Also check legacy single format_preset
        if not selected_formats and base_preset not in ["general", "verbatim"]:
            selected_formats = [base_preset]
        active_format = selected_formats[0] if selected_formats else None
        # Check if active format is in checkboxes or in More dropdown
        self._format_from_more = None
        for key, cb in self.format_checkboxes.items():
            cb.setChecked(key == active_format)
        if active_format and active_format not in self.format_checkboxes:
            # Format is from the More dropdown - find and select it
            self._format_from_more = active_format
            for i in range(self.format_combo.count()):
                if self.format_combo.itemData(i) == active_format:
                    self.format_combo.setCurrentIndex(i)
                    break
        else:
            self.format_combo.setCurrentIndex(0)

        # Tone selection (mutually exclusive radio buttons)
        selected_tones = getattr(self.config, 'selected_tones', [])
        if selected_tones and selected_tones[0] in self.tone_buttons:
            self.tone_buttons[selected_tones[0]].setChecked(True)
        else:
            self.tone_buttons["default"].setChecked(True)

        # Style selection (multi-select checkboxes)
        selected_styles = getattr(self.config, 'selected_styles', [])
        for key, cb in self.style_checkboxes.items():
            cb.setChecked(key in selected_styles)

        # Stacks selection defaults to "None"
        self.stacks_combo.setCurrentIndex(0)

        self._block_all_signals(False)
        self._update_summaries()

    def _save_to_config(self):
        """Save current settings to config."""
        # Save base preset and translation mode
        if self.base_buttons["translation"].isChecked():
            self.config.translation_mode_enabled = True
            self.config.format_preset = "general"  # Use general cleanup when translating
        elif self.base_buttons["verbatim"].isChecked():
            self.config.translation_mode_enabled = False
            self.config.format_preset = "verbatim"
        else:
            self.config.translation_mode_enabled = False
            self.config.format_preset = "general"

        # Save format (mutually exclusive - only one at a time)
        selected_format = None
        for key, cb in self.format_checkboxes.items():
            if cb.isChecked():
                selected_format = key
                break
        # Check if a format was selected from the More dropdown
        if not selected_format and self._format_from_more:
            selected_format = self._format_from_more

        if selected_format:
            self.config.format_preset = selected_format
            self.config.selected_formats = [selected_format]
        else:
            # No format selected - keep base preset (general/verbatim)
            self.config.selected_formats = []

        # Save tone (mutually exclusive)
        selected_tones = []
        for key, radio in self.tone_buttons.items():
            if radio.isChecked() and key != "default":
                selected_tones.append(key)
                break
        self.config.selected_tones = selected_tones

        # Save styles from checkboxes (multi-select)
        selected_styles = []
        for key, cb in self.style_checkboxes.items():
            if cb.isChecked():
                selected_styles.append(key)
        self.config.selected_styles = selected_styles

    def _block_all_signals(self, block: bool):
        """Block or unblock signals from all widgets."""
        self.base_button_group.blockSignals(block)
        self.format_combo.blockSignals(block)
        self.tone_button_group.blockSignals(block)
        for cb in self.format_checkboxes.values():
            cb.blockSignals(block)
        for cb in self.style_checkboxes.values():
            cb.blockSignals(block)
        self.stacks_combo.blockSignals(block)

    def _update_summaries(self):
        """Update accordion header summaries with current selections."""
        # Style summary - count selected checkboxes
        style_count = sum(1 for cb in self.style_checkboxes.values() if cb.isChecked())
        if style_count > 0:
            self.style_section.set_summary(f"{style_count} selected")
        else:
            self.style_section.set_summary("")

        # Stacks summary
        stack_name = self.stacks_combo.currentData()
        if stack_name:
            self.stacks_section.set_summary(stack_name)
        else:
            self.stacks_section.set_summary("")

    def _on_reset_clicked(self):
        """Reset stack to General with no modifiers."""
        self._block_all_signals(True)


        self.base_buttons["general"].setChecked(True)
        self.config.translation_mode_enabled = False

        # Reset formats
        for cb in self.format_checkboxes.values():
            cb.setChecked(False)
        self.format_combo.setCurrentIndex(0)
        self._format_from_more = None

        # Reset tone to Default
        self.tone_buttons["default"].setChecked(True)

        # Reset styles
        for cb in self.style_checkboxes.values():
            cb.setChecked(False)

        # Reset stacks
        self.stacks_combo.setCurrentIndex(0)

        self._block_all_signals(False)

        self._save_to_config()
        self._update_summaries()
        self._announce_tts('default_prompt_configured')
        self.prompt_changed.emit()

    def apply_stack(self, stack: PromptStack):
        """Apply a prompt stack to the current selection.

        Sets format, tone, and style based on the elements in the stack.
        """
        self._block_all_signals(True)

        # Extract elements by category from the stack
        format_keys = []
        tone_keys = []
        style_keys = []

        for element_key in stack.elements:
            if element_key in ALL_ELEMENTS:
                element = ALL_ELEMENTS[element_key]
                if element.category == "format":
                    format_keys.append(element_key)
                elif element.category == "style":
                    # Style elements like "casual", "formal" are tones in our UI
                    if element_key in ["casual", "formal", "professional", "friendly", "enthusiastic", "empathetic"]:
                        tone_keys.append(element_key)
                    else:
                        style_keys.append(element_key)
                elif element.category == "grammar":
                    # Grammar elements don't map to our UI directly
                    pass

        # Apply format (mutually exclusive - use first format key only)
        active_format = format_keys[0] if format_keys else None
        for key, cb in self.format_checkboxes.items():
            cb.setChecked(key == active_format)
        self.format_combo.setCurrentIndex(0)
        self._format_from_more = None

        # Apply tone (radio buttons - use first matching tone or default)
        applied_tone = False
        for key in tone_keys:
            if key in self.tone_buttons:
                self.tone_buttons[key].setChecked(True)
                applied_tone = True
                break
        if not applied_tone:
            self.tone_buttons["default"].setChecked(True)

        # Apply styles (checkboxes)
        for key, cb in self.style_checkboxes.items():
            cb.setChecked(key in style_keys)

        self._block_all_signals(False)

        self._save_to_config()
        self._update_summaries()
        self.prompt_changed.emit()

    def select_format(self, format_key: str):
        """Programmatically select a format by key.

        Works for both quick-option checkboxes and 'More' dropdown formats.
        """
        # Check if it's one of the quick-option checkboxes
        if format_key in self.format_checkboxes:
            self.format_checkboxes[format_key].setChecked(True)
            # _on_format_checkbox_changed handles unchecking others + saving
        else:
            # It's a format from the "More" dropdown
            idx = self.format_combo.findData(format_key)
            if idx >= 0:
                self.format_combo.setCurrentIndex(idx)
                # _on_format_combo_changed handles clearing checkboxes + saving

    def select_tone(self, tone_key: str):
        """Programmatically select a tone by key."""
        if tone_key in self.tone_buttons:
            self.tone_buttons[tone_key].setChecked(True)
            self._on_tone_changed()

    def clear_format(self):
        """Clear all format selections (revert to general)."""
        self._block_format_signals(True)
        for cb in self.format_checkboxes.values():
            cb.setChecked(False)
        self._block_format_signals(False)
        self._format_from_more = None
        self.format_combo.blockSignals(True)
        self.format_combo.setCurrentIndex(0)
        self.format_combo.blockSignals(False)
        self._on_setting_changed()

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
