"""
Prompt Stack Management Dialog

Modal dialog for creating, editing, and managing prompt stacks.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QTextEdit,
    QLineEdit, QMessageBox, QGroupBox, QFormLayout,
    QFileDialog, QFrame, QCheckBox, QScrollArea,
    QWidget, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
import json

from .prompt_elements import (
    FORMAT_ELEMENTS, STYLE_ELEMENTS, GRAMMAR_ELEMENTS,
    PromptStack, get_all_stacks, save_custom_stack,
    delete_stack, build_prompt_from_elements
)


class StackManagerDialog(QDialog):
    """Dialog for managing prompt stacks."""

    stacks_changed = pyqtSignal()  # Emitted when stacks are modified

    def __init__(self, config_dir: Path, parent=None):
        super().__init__(parent)
        self.config_dir = config_dir
        self.current_stack = None
        self.element_checkboxes = {}  # key -> QCheckBox

        self.setWindowTitle("Manage Prompt Stacks")
        self.setModal(True)
        self.resize(900, 650)

        self._init_ui()
        self._load_stacks()

    def _init_ui(self):
        """Initialize the UI."""
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Left panel: Stack list
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)

        list_header = QLabel("<b>Prompt Stacks</b>")
        list_header.setFont(QFont("Sans", 12, QFont.Weight.Bold))
        left_panel.addWidget(list_header)

        self.stack_list = QListWidget()
        self.stack_list.setMinimumWidth(250)
        self.stack_list.currentItemChanged.connect(self._on_stack_selected)
        left_panel.addWidget(self.stack_list)

        # Buttons below list
        list_buttons = QHBoxLayout()
        list_buttons.setSpacing(6)

        new_btn = QPushButton("➕ New")
        new_btn.clicked.connect(self._create_new_stack)
        list_buttons.addWidget(new_btn)

        import_btn = QPushButton("📁 Import")
        import_btn.clicked.connect(self._import_stack)
        list_buttons.addWidget(import_btn)

        left_panel.addLayout(list_buttons)

        layout.addLayout(left_panel, stretch=1)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #dee2e6;")
        separator.setFixedWidth(1)
        layout.addWidget(separator)

        # Right panel: Stack details
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)

        details_header = QLabel("<b>Stack Details</b>")
        details_header.setFont(QFont("Sans", 12, QFont.Weight.Bold))
        right_panel.addWidget(details_header)

        # Stack info group
        info_group = QGroupBox("Stack Information")
        info_layout = QFormLayout(info_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Stack name (e.g., Quick Email, Dev Notes)")
        info_layout.addRow("Name:", self.name_edit)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Brief description")
        info_layout.addRow("Description:", self.description_edit)

        right_panel.addWidget(info_group)

        # Elements selection
        elements_label = QLabel("<b>Prompt Elements:</b>")
        right_panel.addWidget(elements_label)

        # Scrollable area for element checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)

        # Format elements
        format_group = self._create_element_group(
            "Format Elements",
            "Define the output format",
            FORMAT_ELEMENTS
        )
        scroll_layout.addWidget(format_group)

        # Style elements
        style_group = self._create_element_group(
            "Style Elements",
            "Define writing style",
            STYLE_ELEMENTS
        )
        scroll_layout.addWidget(style_group)

        # Grammar elements
        grammar_group = self._create_element_group(
            "Grammar & Structure",
            "Grammar and structural preferences",
            GRAMMAR_ELEMENTS
        )
        scroll_layout.addWidget(grammar_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        right_panel.addWidget(scroll, stretch=1)

        # Action buttons
        action_buttons = QHBoxLayout()
        action_buttons.setSpacing(8)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self._save_current_stack)
        self.save_btn.setEnabled(False)
        action_buttons.addWidget(self.save_btn)

        self.preview_btn = QPushButton("👁️ Preview")
        self.preview_btn.clicked.connect(self._preview_stack)
        self.preview_btn.setEnabled(False)
        action_buttons.addWidget(self.preview_btn)

        self.export_btn = QPushButton("📤 Export")
        self.export_btn.clicked.connect(self._export_stack)
        self.export_btn.setEnabled(False)
        action_buttons.addWidget(self.export_btn)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self._delete_stack)
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

    def _create_element_group(self, title: str, description: str, elements: dict) -> QGroupBox:
        """Create a group box for a category of elements."""
        group = QGroupBox(title)
        group_layout = QVBoxLayout()

        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        desc_label.setWordWrap(True)
        group_layout.addWidget(desc_label)

        # Checkboxes for each element
        for key, element in elements.items():
            checkbox = QCheckBox(element.name)
            checkbox.setProperty("element_key", key)
            checkbox.setToolTip(element.description)
            checkbox.stateChanged.connect(self._on_element_toggled)
            self.element_checkboxes[key] = checkbox
            group_layout.addWidget(checkbox)

        group.setLayout(group_layout)
        return group

    def _load_stacks(self):
        """Load all stacks into the list."""
        self.stack_list.clear()

        all_stacks = get_all_stacks(self.config_dir)

        if not all_stacks:
            item = QListWidgetItem("No stacks yet")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(Qt.GlobalColor.gray)
            self.stack_list.addItem(item)
            return

        for stack in all_stacks:
            item = QListWidgetItem(stack.name)
            item.setData(Qt.ItemDataRole.UserRole, stack)
            self.stack_list.addItem(item)

    def _on_stack_selected(self, current, previous):
        """Handle stack selection."""
        if not current:
            self._clear_details()
            return

        stack = current.data(Qt.ItemDataRole.UserRole)
        if not stack:  # "No stacks yet" item
            self._clear_details()
            return

        # Load stack details
        self.current_stack = stack
        self.name_edit.setText(stack.name)
        self.description_edit.setText(stack.description or "")

        # Update checkboxes
        for key, checkbox in self.element_checkboxes.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(key in stack.elements)
            checkbox.blockSignals(False)

        # Enable buttons
        self.save_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def _clear_details(self):
        """Clear the details panel."""
        self.current_stack = None
        self.name_edit.clear()
        self.description_edit.clear()

        for checkbox in self.element_checkboxes.values():
            checkbox.blockSignals(True)
            checkbox.setChecked(False)
            checkbox.blockSignals(False)

        self.save_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def _on_edit_changed(self):
        """Handle edit field changes."""
        # Enable save button if there's content
        has_content = bool(self.name_edit.text().strip())
        self.save_btn.setEnabled(has_content)

    def _on_element_toggled(self):
        """Handle element checkbox toggle."""
        # Enable save and preview buttons
        has_name = bool(self.name_edit.text().strip())
        has_elements = any(cb.isChecked() for cb in self.element_checkboxes.values())

        self.save_btn.setEnabled(has_name and has_elements)
        self.preview_btn.setEnabled(has_elements)

    def _create_new_stack(self):
        """Create a new stack."""
        # Clear current selection and details
        self.stack_list.clearSelection()
        self._clear_details()

        # Enable save button for new stack
        self.save_btn.setEnabled(True)

        # Focus on name field
        self.name_edit.setFocus()

        QMessageBox.information(
            self, "New Stack",
            "Enter the details for your new prompt stack, select elements, then click Save."
        )

    def _save_current_stack(self):
        """Save the current stack."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Name Required", "Please enter a stack name.")
            return

        # Get selected elements
        selected_elements = [
            key for key, checkbox in self.element_checkboxes.items()
            if checkbox.isChecked()
        ]

        if not selected_elements:
            QMessageBox.warning(
                self, "No Elements Selected",
                "Please select at least one element for this stack."
            )
            return

        description = self.description_edit.text().strip()

        # Create stack
        stack = PromptStack(
            name=name,
            elements=selected_elements,
            description=description
        )

        # Save stack
        try:
            save_custom_stack(stack, self.config_dir)
            QMessageBox.information(
                self, "Stack Saved",
                f"Stack '{name}' has been saved successfully."
            )

            # Reload stacks
            self._load_stacks()
            self.stacks_changed.emit()

            # Select the newly saved stack
            for i in range(self.stack_list.count()):
                item = self.stack_list.item(i)
                stack_data = item.data(Qt.ItemDataRole.UserRole)
                if stack_data and stack_data.name == name:
                    self.stack_list.setCurrentItem(item)
                    break

        except Exception as e:
            QMessageBox.critical(
                self, "Save Failed",
                f"Failed to save stack:\n{str(e)}"
            )

    def _preview_stack(self):
        """Preview the generated prompt from current selection."""
        selected_elements = [
            key for key, checkbox in self.element_checkboxes.items()
            if checkbox.isChecked()
        ]

        if not selected_elements:
            QMessageBox.warning(
                self, "No Elements Selected",
                "Please select at least one element to preview."
            )
            return

        prompt = build_prompt_from_elements(selected_elements)

        dialog = QDialog(self)
        dialog.setWindowTitle("Prompt Preview")
        dialog.resize(600, 500)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setPlainText(prompt)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("font-family: monospace; font-size: 11px;")
        layout.addWidget(text_edit)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _export_stack(self):
        """Export the current stack to JSON."""
        if not self.current_stack:
            return

        # Prepare export data
        export_data = {
            "name": self.current_stack.name,
            "description": self.current_stack.description,
            "elements": self.current_stack.elements
        }

        # Ask for save location
        safe_name = self.current_stack.name.lower().replace(" ", "_")
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Stack",
            f"{safe_name}.json",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                QMessageBox.information(
                    self, "Export Successful",
                    f"Stack exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Failed",
                    f"Failed to export stack:\n{str(e)}"
                )

    def _import_stack(self):
        """Import a stack from JSON."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Stack",
            "",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    import_data = json.load(f)

                # Validate data
                required_fields = ["name", "elements"]
                if not all(field in import_data for field in required_fields):
                    raise ValueError("Invalid stack file: missing required fields")

                # Load into UI
                self.name_edit.setText(import_data.get("name", ""))
                self.description_edit.setText(import_data.get("description", ""))

                # Update checkboxes
                imported_elements = import_data.get("elements", [])
                for key, checkbox in self.element_checkboxes.items():
                    checkbox.blockSignals(True)
                    checkbox.setChecked(key in imported_elements)
                    checkbox.blockSignals(False)

                QMessageBox.information(
                    self, "Import Successful",
                    f"Stack '{import_data['name']}' has been imported.\n"
                    "Click Save to add it to your stacks."
                )

                # Enable buttons
                self.save_btn.setEnabled(True)
                self.preview_btn.setEnabled(True)

            except Exception as e:
                QMessageBox.critical(
                    self, "Import Failed",
                    f"Failed to import stack:\n{str(e)}"
                )

    def _delete_stack(self):
        """Delete the current stack."""
        if not self.current_stack:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete the stack '{self.current_stack.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_stack(self.current_stack.name, self.config_dir)
                QMessageBox.information(
                    self, "Stack Deleted",
                    f"Stack '{self.current_stack.name}' has been deleted."
                )

                # Reload stacks
                self._load_stacks()
                self._clear_details()
                self.stacks_changed.emit()

            except Exception as e:
                QMessageBox.critical(
                    self, "Delete Failed",
                    f"Failed to delete stack:\n{str(e)}"
                )
