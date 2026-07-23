"""Output Panel - Single output area for transcription results with queue support.

Provides a single output area with copy button and queue indicator bar.
"""

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)

from .markdown_widget import MarkdownTextWidget
from .clipboard import copy_to_clipboard


class OutputPanel(QWidget):
    """Single output panel with text area, copy button, and queue indicator."""

    copy_clicked = pyqtSignal(int)  # kept for signal compatibility (always emits 0)
    text_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_item_id: Optional[str] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Main output frame
        self._frame = QFrame()
        self._frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self._frame.setStyleSheet("""
            QFrame#outputFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
        """)
        self._frame.setObjectName("outputFrame")

        frame_layout = QVBoxLayout(self._frame)
        frame_layout.setContentsMargins(8, 8, 8, 8)
        frame_layout.setSpacing(4)

        # Header with status and copy button
        header = QHBoxLayout()
        header.setSpacing(8)

        header.addStretch()

        # Status label (shows "Transcribing..." etc.)
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #888; font-size: 10px;")
        header.addWidget(self._status_label)

        # Copy button
        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setFixedSize(50, 24)
        self._copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 11px;
                color: #555;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-color: #bbb;
            }
            QPushButton:pressed {
                background-color: #ddd;
            }
            QPushButton:disabled {
                color: #aaa;
                background-color: #f8f8f8;
            }
        """)
        self._copy_btn.clicked.connect(self._on_copy)
        self._copy_btn.setEnabled(False)
        header.addWidget(self._copy_btn)

        frame_layout.addLayout(header)

        # Text widget
        self.text_widget = MarkdownTextWidget()
        self.text_widget.setPlaceholderText("")
        self.text_widget.setFont(QFont("Sans", 11))
        self.text_widget.setMinimumHeight(60)
        self.text_widget.textChanged.connect(lambda: self.text_changed.emit())
        frame_layout.addWidget(self.text_widget, 1)

        layout.addWidget(self._frame, 1)

        # Queue indicator bar
        self.queue_bar = QFrame()
        self.queue_bar.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-radius: 4px;
            }
        """)
        queue_layout = QHBoxLayout(self.queue_bar)
        queue_layout.setContentsMargins(8, 4, 8, 4)

        self.queue_label = QLabel("")
        self.queue_label.setStyleSheet("color: #666; font-size: 11px;")
        queue_layout.addWidget(self.queue_label)

        queue_layout.addStretch()

        self.queue_bar.hide()
        layout.addWidget(self.queue_bar)

    # -------------------------------------------------------------------------
    # Queue lifecycle methods
    # -------------------------------------------------------------------------

    def on_transcription_started(self, item_id: str):
        """Show transcribing state for a new item.

        Existing text is deliberately preserved — results are appended to it
        by the main window, so clearing here would lose accumulated dictation.
        """
        self._current_item_id = item_id
        if not self.text_widget.toPlainText().strip():
            self.text_widget.setPlaceholderText("Transcribing...")
        self._status_label.setText("Transcribing...")
        self._status_label.setStyleSheet("color: #0d6efd; font-size: 10px;")
        self._copy_btn.setEnabled(False)
        self._frame.setStyleSheet("""
            QFrame#outputFrame {
                background-color: #f8f9ff;
                border: 1px solid #b6d4fe;
                border-radius: 6px;
            }
        """)

    def on_transcription_complete(self, item_id: str):
        """Mark an item complete (styling only).

        The main window owns text placement so results can append to
        existing text instead of replacing it.
        """
        self._current_item_id = item_id
        self._status_label.setText("")
        self._status_label.setStyleSheet("color: #888; font-size: 10px;")
        self._copy_btn.setEnabled(True)
        self._frame.setStyleSheet("""
            QFrame#outputFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
        """)

    def on_transcription_error(self, item_id: str, error: str):
        """Display error state without overwriting accumulated text."""
        self._current_item_id = item_id
        self._status_label.setText(f"Failed: {error[:60]}")
        self._status_label.setStyleSheet("color: #dc3545; font-size: 10px;")
        self._copy_btn.setEnabled(bool(self.text_widget.toPlainText()))
        self._frame.setStyleSheet("""
            QFrame#outputFrame {
                background-color: #fff5f5;
                border: 1px solid #f5c6cb;
                border-radius: 6px;
            }
        """)

    def on_transcription_status(self, item_id: str, status: str):
        """Update status label for an in-progress transcription."""
        if self._current_item_id == item_id:
            self._status_label.setText(status)

    def update_queue_status(self, pending_count: int, active_count: int):
        """Update the queue indicator with current counts."""
        if pending_count > 0:
            self.queue_label.setText(f"Queue: {pending_count} waiting")
            self.queue_bar.show()
        else:
            self.queue_bar.hide()

    # -------------------------------------------------------------------------
    # Public interface (backward compatible)
    # -------------------------------------------------------------------------

    def set_text(self, text: str):
        """Set text in the output area."""
        self.text_widget.setMarkdown(text)
        self._copy_btn.setEnabled(bool(text))
        self._status_label.setText("")
        self._frame.setStyleSheet("""
            QFrame#outputFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
        """)

    def get_primary_text(self) -> str:
        """Get the current output text."""
        return self.text_widget.toPlainText()

    def get_all_text(self) -> str:
        """Get all output text (same as get_primary_text for single panel)."""
        return self.text_widget.toPlainText()

    def clear(self):
        """Reset to empty state."""
        self._current_item_id = None
        self.text_widget.setMarkdown("")
        self.text_widget.setPlaceholderText("")
        self._status_label.setText("")
        self._copy_btn.setEnabled(False)
        self._frame.setStyleSheet("""
            QFrame#outputFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
        """)

    # -------------------------------------------------------------------------
    # Internal
    # -------------------------------------------------------------------------

    def _on_copy(self):
        """Handle copy button click."""
        text = self.text_widget.toPlainText()
        if text:
            copy_to_clipboard(text)
            self.copy_clicked.emit(0)
