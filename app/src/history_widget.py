"""History tab widget for viewing transcription history."""

import subprocess
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .database import get_db, CSV_EXPORT_FILE


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


class HistoryWidget(QWidget):
    """Widget for viewing transcription history."""

    transcription_selected = pyqtSignal(str)  # Keep for API compatibility

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Transcription History")
        title.setFont(QFont("Sans", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Your transcription history is stored locally and can be exported as a CSV file.\n"
            "Click the button below to open the history file in your default spreadsheet application."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Stats section
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.Shape.StyledPanel)
        stats_frame.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 8px; padding: 10px; }")
        stats_layout = QVBoxLayout(stats_frame)

        stats_title = QLabel("Statistics")
        stats_title.setFont(QFont("Sans", 11, QFont.Weight.Bold))
        stats_layout.addWidget(stats_title)

        self.count_label = QLabel("")
        stats_layout.addWidget(self.count_label)

        self.storage_label = QLabel("")
        stats_layout.addWidget(self.storage_label)

        self.audio_label = QLabel("")
        stats_layout.addWidget(self.audio_label)

        layout.addWidget(stats_frame)

        # Buttons
        button_layout = QHBoxLayout()

        self.open_btn = QPushButton("Open History File")
        self.open_btn.setMinimumHeight(45)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.open_btn.clicked.connect(self.open_history_file)
        button_layout.addWidget(self.open_btn)

        button_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setMinimumHeight(38)
        refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        # File location info
        file_info = QLabel(f"History file: {CSV_EXPORT_FILE}")
        file_info.setStyleSheet("color: #888; font-size: 10px; margin-top: 10px;")
        file_info.setWordWrap(True)
        layout.addWidget(file_info)

        layout.addStretch()

    def refresh(self):
        """Refresh the statistics display."""
        db = get_db()
        stats = db.get_storage_stats()

        self.count_label.setText(f"Total transcriptions: {stats['total_records']}")
        self.storage_label.setText(
            f"Database size: {format_size(stats['db_size_bytes'])}"
        )
        self.audio_label.setText(
            f"Audio archive: {format_size(stats['audio_size_bytes'])} ({stats['records_with_audio']} recordings)"
        )

        # Enable/disable open button based on whether there are records
        self.open_btn.setEnabled(stats['total_records'] > 0)

    def open_history_file(self):
        """Export history to CSV and open it."""
        try:
            db = get_db()
            filepath = db.export_to_csv()

            # Open with system default application
            if sys.platform == 'darwin':
                subprocess.run(['open', str(filepath)])
            elif sys.platform == 'win32':
                subprocess.run(['start', '', str(filepath)], shell=True)
            else:
                # Linux - use xdg-open
                subprocess.run(['xdg-open', str(filepath)])

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open history file: {e}"
            )
