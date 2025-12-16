"""Formats tab for managing output format presets."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QScrollArea, QFrame,
    QSizePolicy, QGroupBox, QLineEdit, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .config import (
    Config, FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES, FORMAT_CATEGORIES,
    save_config
)


class FormatCard(QFrame):
    """A card widget for displaying a format preset."""

    format_selected = pyqtSignal(str)  # format_key

    def __init__(self, format_key: str, format_data: dict, is_selected: bool = False, parent=None):
        super().__init__(parent)
        self.format_key = format_key
        self.format_data = format_data
        self.is_selected = is_selected

        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 10, 12, 10)

        # Format name
        name_label = QLabel(FORMAT_DISPLAY_NAMES.get(format_key, format_key))
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(name_label)

        # Description
        description = format_data.get("description", "")
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #666; font-size: 11px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # Instruction preview (first 100 chars)
        instruction = format_data.get("instruction", "")
        if instruction:
            preview = instruction[:100] + "..." if len(instruction) > 100 else instruction
            inst_label = QLabel(f"📝 {preview}")
            inst_label.setStyleSheet("color: #495057; font-size: 10px; margin-top: 4px;")
            inst_label.setWordWrap(True)
            layout.addWidget(inst_label)

    def _update_style(self):
        """Update card style based on selection state."""
        if self.is_selected:
            self.setStyleSheet("""
                FormatCard {
                    background-color: #007bff;
                    border: 2px solid #0056b3;
                    border-radius: 8px;
                    padding: 4px;
                }
                QLabel {
                    color: white;
                }
            """)
        else:
            self.setStyleSheet("""
                FormatCard {
                    background-color: #f8f9fa;
                    border: 2px solid #dee2e6;
                    border-radius: 8px;
                    padding: 4px;
                }
                FormatCard:hover {
                    background-color: #e9ecef;
                    border-color: #adb5bd;
                }
            """)

    def mousePressEvent(self, event):
        """Handle card click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.format_selected.emit(self.format_key)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        """Update selection state."""
        self.is_selected = selected
        self._update_style()


class FormatsWidget(QWidget):
    """Widget for managing format presets."""

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.format_cards = {}  # format_key -> FormatCard

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Format Presets")
        title.setFont(QFont("Sans", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Description
        desc = QLabel(
            "Select a format preset to structure your transcriptions. "
            "Each format includes specific formatting and adherence instructions."
        )
        desc.setStyleSheet("color: #666; margin-bottom: 8px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Writing sample section
        writing_sample_group = QGroupBox("Writing Style Reference (Optional)")
        writing_sample_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ced4da;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        ws_layout = QVBoxLayout(writing_sample_group)

        ws_desc = QLabel(
            "Provide a sample of your writing to guide the AI's output style. "
            "The AI will use this as a reference for tone, structure, and formatting conventions."
        )
        ws_desc.setStyleSheet("color: #495057; font-weight: normal; font-size: 11px;")
        ws_desc.setWordWrap(True)
        ws_layout.addWidget(ws_desc)

        self.writing_sample_edit = QTextEdit()
        self.writing_sample_edit.setPlaceholderText(
            "Paste a sample of your writing here (e.g., a paragraph from a previous document). "
            "This helps the AI match your personal style."
        )
        self.writing_sample_edit.setMaximumHeight(120)
        self.writing_sample_edit.setText(self.config.writing_sample)
        self.writing_sample_edit.textChanged.connect(self._on_writing_sample_changed)
        ws_layout.addWidget(self.writing_sample_edit)

        layout.addWidget(writing_sample_group)

        # Format presets by category
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        scroll_layout.setContentsMargins(0, 0, 8, 0)

        # Organize formats by category
        formats_by_category = {}
        for format_key, format_data in FORMAT_TEMPLATES.items():
            category = format_data.get("category", "general")
            if category not in formats_by_category:
                formats_by_category[category] = []
            formats_by_category[category].append((format_key, format_data))

        # Create sections for each category
        for category_key, category_name in FORMAT_CATEGORIES.items():
            if category_key not in formats_by_category:
                continue

            # Category header
            category_label = QLabel(category_name)
            category_label.setFont(QFont("Sans", 13, QFont.Weight.Bold))
            category_label.setStyleSheet("color: #212529; margin-top: 8px;")
            scroll_layout.addWidget(category_label)

            # Format cards in this category
            category_layout = QHBoxLayout()
            category_layout.setSpacing(12)

            for format_key, format_data in formats_by_category[category_key]:
                is_selected = (format_key == self.config.format_preset)
                card = FormatCard(format_key, format_data, is_selected, self)
                card.format_selected.connect(self._on_format_selected)
                card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
                self.format_cards[format_key] = card
                category_layout.addWidget(card)

            # Add stretch to prevent cards from stretching too wide
            category_layout.addStretch()
            scroll_layout.addLayout(category_layout)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)

        # Format details panel
        details_group = QGroupBox("Selected Format Details")
        details_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #007bff;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #007bff;
            }
        """)
        details_layout = QVBoxLayout(details_group)

        self.format_name_label = QLabel()
        self.format_name_label.setFont(QFont("Sans", 13, QFont.Weight.Bold))
        details_layout.addWidget(self.format_name_label)

        self.format_instruction_label = QLabel()
        self.format_instruction_label.setStyleSheet("color: #495057; margin-top: 4px;")
        self.format_instruction_label.setWordWrap(True)
        details_layout.addWidget(self.format_instruction_label)

        adherence_label = QLabel("Format Adherence:")
        adherence_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        details_layout.addWidget(adherence_label)

        self.format_adherence_label = QLabel()
        self.format_adherence_label.setStyleSheet("color: #495057;")
        self.format_adherence_label.setWordWrap(True)
        details_layout.addWidget(self.format_adherence_label)

        layout.addWidget(details_group)

        # Update details with current format
        self._update_format_details()

    def _on_format_selected(self, format_key: str):
        """Handle format selection."""
        # Update config
        self.config.format_preset = format_key
        save_config(self.config)

        # Update card selection states
        for key, card in self.format_cards.items():
            card.set_selected(key == format_key)

        # Update details panel
        self._update_format_details()

    def _update_format_details(self):
        """Update the format details panel."""
        format_key = self.config.format_preset
        format_data = FORMAT_TEMPLATES.get(format_key, {})

        display_name = FORMAT_DISPLAY_NAMES.get(format_key, format_key)
        self.format_name_label.setText(f"📄 {display_name}")

        instruction = format_data.get("instruction", "No specific instructions")
        self.format_instruction_label.setText(instruction or "Uses base cleanup only")

        adherence = format_data.get("adherence", "")
        self.format_adherence_label.setText(adherence or "No specific adherence requirements")

    def _on_writing_sample_changed(self):
        """Handle writing sample text changes."""
        self.config.writing_sample = self.writing_sample_edit.toPlainText()
        save_config(self.config)

    def refresh(self):
        """Refresh the widget state from config."""
        # Update card selection states
        for key, card in self.format_cards.items():
            card.set_selected(key == self.config.format_preset)

        # Update details
        self._update_format_details()

        # Update writing sample
        self.writing_sample_edit.setText(self.config.writing_sample)
