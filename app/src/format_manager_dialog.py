"""
Format Management Dialog

Modal dialog for creating, editing, and managing custom format presets.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QTextEdit,
    QLineEdit, QMessageBox, QGroupBox, QFormLayout,
    QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
import json

from .config import (
    Config, FORMAT_TEMPLATES, FORMAT_DISPLAY_NAMES,
    FORMAT_CATEGORIES, save_config
)


class FormatManagerDialog(QDialog):
    """Dialog for managing format presets."""

    formats_changed = pyqtSignal()  # Emitted when formats are modified

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Manage Format Presets")
        self.setModal(True)
        self.resize(800, 600)

        self._init_ui()
        self._load_formats()

    def _init_ui(self):
        """Initialize the UI."""
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Left panel: Format list
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)

        list_header = QLabel("<b>Format Presets</b>")
        list_header.setFont(QFont("Sans", 12, QFont.Weight.Bold))
        left_panel.addWidget(list_header)

        self.format_list = QListWidget()
        self.format_list.setMinimumWidth(250)
        self.format_list.currentItemChanged.connect(self._on_format_selected)
        left_panel.addWidget(self.format_list)

        # Buttons below list
        list_buttons = QHBoxLayout()
        list_buttons.setSpacing(6)

        new_btn = QPushButton("➕ New")
        new_btn.clicked.connect(self._create_new_format)
        list_buttons.addWidget(new_btn)

        import_btn = QPushButton("📁 Import")
        import_btn.clicked.connect(self._import_format)
        list_buttons.addWidget(import_btn)

        left_panel.addLayout(list_buttons)

        layout.addLayout(left_panel, stretch=1)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #dee2e6;")
        separator.setFixedWidth(1)
        layout.addWidget(separator)

        # Right panel: Format details
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)

        details_header = QLabel("<b>Format Details</b>")
        details_header.setFont(QFont("Sans", 12, QFont.Weight.Bold))
        right_panel.addWidget(details_header)

        # Format info group
        info_group = QGroupBox("Format Information")
        info_layout = QFormLayout(info_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Format name")
        info_layout.addRow("Name:", self.name_edit)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Brief description")
        info_layout.addRow("Description:", self.description_edit)

        right_panel.addWidget(info_group)

        # Instruction text
        instruction_label = QLabel("<b>Instruction Text:</b>")
        right_panel.addWidget(instruction_label)

        self.instruction_edit = QTextEdit()
        self.instruction_edit.setPlaceholderText(
            "Enter the formatting instructions for this preset.\n"
            "Example: Format as a professional email with proper greeting and sign-off."
        )
        self.instruction_edit.setMinimumHeight(120)
        right_panel.addWidget(self.instruction_edit)

        # Adherence text
        adherence_label = QLabel("<b>Adherence Instructions:</b>")
        right_panel.addWidget(adherence_label)

        self.adherence_edit = QTextEdit()
        self.adherence_edit.setPlaceholderText(
            "Enter specific adherence instructions (optional).\n"
            "Example: Always use proper email headers and maintain professional tone."
        )
        self.adherence_edit.setMinimumHeight(100)
        right_panel.addWidget(self.adherence_edit)

        # Action buttons
        action_buttons = QHBoxLayout()
        action_buttons.setSpacing(8)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self._save_current_format)
        self.save_btn.setEnabled(False)
        action_buttons.addWidget(self.save_btn)

        self.export_btn = QPushButton("📤 Export")
        self.export_btn.clicked.connect(self._export_format)
        self.export_btn.setEnabled(False)
        action_buttons.addWidget(self.export_btn)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self._delete_format)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("color: #dc3545;")
        action_buttons.addWidget(self.delete_btn)

        action_buttons.addStretch()

        right_panel.addLayout(action_buttons)

        # Bottom: Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        right_panel.addWidget(close_btn)

        layout.addLayout(right_panel, stretch=2)

        # Connect text change signals
        self.name_edit.textChanged.connect(self._on_edit_changed)
        self.description_edit.textChanged.connect(self._on_edit_changed)
        self.instruction_edit.textChanged.connect(self._on_edit_changed)
        self.adherence_edit.textChanged.connect(self._on_edit_changed)

    def _load_formats(self):
        """Load all formats into the list."""
        self.format_list.clear()

        # Group formats by category
        for category_key, category_name in FORMAT_CATEGORIES.items():
            # Add category header
            category_item = QListWidgetItem(f"── {category_name} ──")
            category_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Not selectable
            category_item.setFont(QFont("Sans", 10, QFont.Weight.Bold))
            category_item.setForeground(Qt.GlobalColor.gray)
            self.format_list.addItem(category_item)

            # Add formats in this category
            for format_key, format_data in FORMAT_TEMPLATES.items():
                if format_data.get("category") == category_key:
                    display_name = FORMAT_DISPLAY_NAMES.get(format_key, format_key)
                    item = QListWidgetItem(f"  {display_name}")
                    item.setData(Qt.ItemDataRole.UserRole, format_key)
                    self.format_list.addItem(item)

    def _on_format_selected(self, current, previous):
        """Handle format selection."""
        if not current:
            self._clear_details()
            return

        format_key = current.data(Qt.ItemDataRole.UserRole)
        if not format_key:  # Category header
            self._clear_details()
            return

        # Load format details
        format_data = FORMAT_TEMPLATES.get(format_key, {})
        display_name = FORMAT_DISPLAY_NAMES.get(format_key, format_key)

        self.name_edit.setText(display_name)
        self.description_edit.setText(format_data.get("description", ""))
        self.instruction_edit.setPlainText(format_data.get("instruction", ""))
        self.adherence_edit.setPlainText(format_data.get("adherence", ""))

        # Enable buttons
        self.save_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        # Only allow deleting custom formats (not built-in ones)
        is_custom = format_key.startswith("custom_")
        self.delete_btn.setEnabled(is_custom)

    def _clear_details(self):
        """Clear the details panel."""
        self.name_edit.clear()
        self.description_edit.clear()
        self.instruction_edit.clear()
        self.adherence_edit.clear()
        self.save_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def _on_edit_changed(self):
        """Handle edit field changes."""
        # Enable save button if there's content
        has_content = bool(self.name_edit.text().strip())
        self.save_btn.setEnabled(has_content)

    def _create_new_format(self):
        """Create a new format preset."""
        # Clear current selection and details
        self.format_list.clearSelection()
        self._clear_details()

        # Enable save button for new format
        self.save_btn.setEnabled(True)

        # Focus on name field
        self.name_edit.setFocus()

        QMessageBox.information(
            self, "New Format",
            "Enter the details for your new format preset, then click Save."
        )

    def _save_current_format(self):
        """Save the current format."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Name Required", "Please enter a format name.")
            return

        description = self.description_edit.text().strip()
        instruction = self.instruction_edit.toPlainText().strip()
        adherence = self.adherence_edit.toPlainText().strip()

        # Generate format key
        format_key = name.lower().replace(" ", "_")
        if not format_key.startswith("custom_"):
            format_key = f"custom_{format_key}"

        # Create format data
        format_data = {
            "description": description,
            "instruction": instruction,
            "adherence": adherence,
            "category": "custom"
        }

        # Save to config (this would need to be implemented in config.py)
        # For now, show a message
        QMessageBox.information(
            self, "Format Saved",
            f"Format '{name}' has been saved.\n\n"
            "Note: Custom format persistence needs to be implemented in config.py"
        )

        # Reload formats
        self._load_formats()
        self.formats_changed.emit()

    def _export_format(self):
        """Export the current format to JSON."""
        current_item = self.format_list.currentItem()
        if not current_item:
            return

        format_key = current_item.data(Qt.ItemDataRole.UserRole)
        if not format_key:
            return

        # Get format data
        format_data = FORMAT_TEMPLATES.get(format_key, {})
        display_name = FORMAT_DISPLAY_NAMES.get(format_key, format_key)

        # Prepare export data
        export_data = {
            "name": display_name,
            "key": format_key,
            "description": format_data.get("description", ""),
            "instruction": format_data.get("instruction", ""),
            "adherence": format_data.get("adherence", ""),
            "category": format_data.get("category", "custom")
        }

        # Ask for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Format",
            f"{format_key}.json",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                QMessageBox.information(
                    self, "Export Successful",
                    f"Format exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Failed",
                    f"Failed to export format:\n{str(e)}"
                )

    def _import_format(self):
        """Import a format from JSON."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Format",
            "",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    import_data = json.load(f)

                # Validate data
                required_fields = ["name", "key"]
                if not all(field in import_data for field in required_fields):
                    raise ValueError("Invalid format file: missing required fields")

                # Load into UI
                self.name_edit.setText(import_data.get("name", ""))
                self.description_edit.setText(import_data.get("description", ""))
                self.instruction_edit.setPlainText(import_data.get("instruction", ""))
                self.adherence_edit.setPlainText(import_data.get("adherence", ""))

                QMessageBox.information(
                    self, "Import Successful",
                    f"Format '{import_data['name']}' has been imported.\n"
                    "Click Save to add it to your presets."
                )

            except Exception as e:
                QMessageBox.critical(
                    self, "Import Failed",
                    f"Failed to import format:\n{str(e)}"
                )

    def _delete_format(self):
        """Delete the current format."""
        current_item = self.format_list.currentItem()
        if not current_item:
            return

        format_key = current_item.data(Qt.ItemDataRole.UserRole)
        if not format_key or not format_key.startswith("custom_"):
            QMessageBox.warning(
                self, "Cannot Delete",
                "Only custom formats can be deleted."
            )
            return

        display_name = FORMAT_DISPLAY_NAMES.get(format_key, format_key)

        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete the format '{display_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Delete format (this would need to be implemented in config.py)
            QMessageBox.information(
                self, "Format Deleted",
                f"Format '{display_name}' has been deleted.\n\n"
                "Note: Custom format deletion needs to be implemented in config.py"
            )

            # Reload formats
            self._load_formats()
            self._clear_details()
            self.formats_changed.emit()
