"""History tab widget for browsing and retrieving past transcriptions."""

from datetime import datetime, date
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QFrame,
    QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .database_mongo import get_db, TranscriptionRecord
from .audio_feedback import get_feedback
from .config import Config


def format_relative_time(timestamp_str: str) -> str:
    """Format timestamp as relative time (Today, Yesterday, X days ago, or date)."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        dt_date = dt.date()
        today = date.today()
        delta = (today - dt_date).days

        if delta == 0:
            # Today - show "Today at HH:MM"
            return f"Today at {dt.strftime('%H:%M')}"
        elif delta == 1:
            return "Yesterday"
        elif delta <= 7:
            return f"{delta} days ago"
        else:
            # Older - show date only
            return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return timestamp_str[:16] if timestamp_str else "Unknown"


def format_date_header(record_date: date) -> str:
    """Format a date for display in a date divider header."""
    today = date.today()
    delta = (today - record_date).days

    if delta == 0:
        return "Today"
    elif delta == 1:
        return "Yesterday"
    else:
        # Show day name for the current week, full date otherwise
        if delta < 7:
            return record_date.strftime("%A")  # e.g., "Monday"
        else:
            return record_date.strftime("%A, %B %d, %Y")  # e.g., "Monday, December 28, 2025"


def get_preview_text(text: str, max_chars: int = 120) -> str:
    """Get preview text, truncating at max_chars with ellipsis if needed."""
    clean_text = text.replace("\n", " ").strip()
    # Collapse multiple spaces
    clean_text = " ".join(clean_text.split())
    if len(clean_text) <= max_chars:
        return clean_text
    # Truncate at word boundary
    truncated = clean_text[:max_chars].rsplit(" ", 1)[0]
    return truncated + "..."


class DateDivider(QFrame):
    """A horizontal divider with a date label for separating days in history."""

    def __init__(self, label_text: str, parent=None):
        super().__init__(parent)
        self.setup_ui(label_text)

    def setup_ui(self, label_text: str):
        self.setFixedHeight(32)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 4)
        layout.setSpacing(12)

        # Left line
        left_line = QFrame()
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setStyleSheet("background-color: #ccc;")
        left_line.setFixedHeight(1)
        layout.addWidget(left_line, 1)

        # Date label
        label = QLabel(label_text)
        label.setStyleSheet("color: #666; font-size: 11px; font-weight: bold;")
        layout.addWidget(label)

        # Right line
        right_line = QFrame()
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setStyleSheet("background-color: #ccc;")
        right_line.setFixedHeight(1)
        layout.addWidget(right_line, 1)


class TranscriptItem(QFrame):
    """A single transcript item in the history list."""

    copy_clicked = pyqtSignal(object)  # Emits the TranscriptionRecord

    def __init__(self, record: TranscriptionRecord, parent=None):
        super().__init__(parent)
        self.record = record
        self.setup_ui()

    def setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            TranscriptItem {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            TranscriptItem:hover {
                background-color: #f8f9fa;
            }
        """)
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 8, 8, 8)

        # Preview text (two lines, larger font)
        preview_text = get_preview_text(self.record.transcript_text, 140)
        preview = QLabel(preview_text)
        preview.setWordWrap(True)
        preview.setStyleSheet("color: #333; font-size: 13px;")
        layout.addWidget(preview, 1)  # Stretch factor 1 to take available space

        # Right side: timestamp and copy button
        right_layout = QVBoxLayout()
        right_layout.setSpacing(4)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Timestamp
        time_str = format_relative_time(self.record.timestamp)
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #888; font-size: 11px;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(time_label)

        # Clipboard button
        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(28, 28)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setToolTip("Copy to clipboard")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e8f4fd;
                border-color: #007bff;
            }
            QPushButton:pressed {
                background-color: #cce5ff;
            }
        """)
        copy_btn.clicked.connect(lambda: self.copy_clicked.emit(self.record))
        right_layout.addWidget(copy_btn, 0, Qt.AlignmentFlag.AlignRight)

        layout.addLayout(right_layout)


class HistoryWidget(QWidget):
    """Widget for browsing and retrieving past transcriptions."""

    transcription_selected = pyqtSignal(str)  # Kept for API compatibility

    def __init__(self, config: Config = None, parent=None):
        super().__init__(parent)
        self.config = config
        self.current_search = ""
        self.current_offset = 0
        self.page_size = 10
        self.total_count = 0
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header with title and search
        header = QHBoxLayout()

        title = QLabel("Transcriptions")
        title.setFont(QFont("Sans", 14, QFont.Weight.Bold))
        header.addWidget(title)

        header.addStretch()

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search transcriptions...")
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        self.search_input.returnPressed.connect(self._on_search)
        header.addWidget(self.search_input)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._on_search)
        header.addWidget(search_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._on_clear_search)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Scrollable list of transcripts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f5f5f5;
            }
        """)

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(4)
        self.list_layout.setContentsMargins(8, 8, 8, 8)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll, 1)

        # Pagination controls
        pagination = QHBoxLayout()

        self.start_btn = QPushButton("⏮ Start")
        self.start_btn.clicked.connect(self._on_start)
        self.start_btn.setEnabled(False)
        pagination.addWidget(self.start_btn)

        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.clicked.connect(self._on_prev_page)
        self.prev_btn.setEnabled(False)
        pagination.addWidget(self.prev_btn)

        pagination.addStretch()

        self.page_label = QLabel("Page 1")
        self.page_label.setStyleSheet("color: #666;")
        pagination.addWidget(self.page_label)

        pagination.addStretch()

        self.next_btn = QPushButton("Next →")
        self.next_btn.clicked.connect(self._on_next_page)
        pagination.addWidget(self.next_btn)

        layout.addLayout(pagination)

        # Status bar
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)

    def refresh(self):
        """Refresh the transcript list."""
        db = get_db()

        # Get total count
        self.total_count = db.get_total_count(search=self.current_search if self.current_search else None)

        # Get transcripts for current page
        records = db.get_transcriptions(
            limit=self.page_size,
            offset=self.current_offset,
            search=self.current_search if self.current_search else None,
        )

        # Clear existing items
        while self.list_layout.count() > 1:  # Keep the stretch
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new items with date dividers
        current_date = None
        for record in records:
            # Parse the record's date
            try:
                record_dt = datetime.fromisoformat(record.timestamp)
                record_date = record_dt.date()
            except (ValueError, TypeError):
                record_date = None

            # Insert date divider when date changes (except for the first item on page 1)
            if record_date and record_date != current_date:
                # Only skip "Today" divider on page 1 for the very first items
                should_show_divider = not (
                    self.current_offset == 0
                    and current_date is None
                    and record_date == date.today()
                )
                if should_show_divider:
                    divider = DateDivider(format_date_header(record_date))
                    self.list_layout.insertWidget(self.list_layout.count() - 1, divider)
                current_date = record_date

            item = TranscriptItem(record)
            item.copy_clicked.connect(self._on_copy)
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)

        # Update pagination
        current_page = (self.current_offset // self.page_size) + 1
        total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"Page {current_page} of {total_pages}")
        self.start_btn.setEnabled(self.current_offset > 0)
        self.prev_btn.setEnabled(self.current_offset > 0)
        self.next_btn.setEnabled(self.current_offset + self.page_size < self.total_count)

        # Update status
        if self.current_search:
            self.status_label.setText(f"Found {self.total_count} transcriptions matching \"{self.current_search}\"")
        else:
            self.status_label.setText(f"{self.total_count} transcriptions total")

    def _on_search(self):
        """Handle search."""
        self.current_search = self.search_input.text().strip()
        self.current_offset = 0
        self.refresh()

    def _on_clear_search(self):
        """Clear search and show all."""
        self.search_input.clear()
        self.current_search = ""
        self.current_offset = 0
        self.refresh()

    def _on_start(self):
        """Go to the first page (newest transcriptions)."""
        self.current_offset = 0
        self.refresh()

    def _on_prev_page(self):
        """Go to previous page."""
        self.current_offset = max(0, self.current_offset - self.page_size)
        self.refresh()

    def _on_next_page(self):
        """Go to next page."""
        self.current_offset += self.page_size
        self.refresh()

    def _on_copy(self, record: TranscriptionRecord):
        """Copy transcript to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(record.transcript_text)

        # Play clipboard feedback
        if self.config:
            feedback = get_feedback()
            feedback.enabled = self.config.beep_on_clipboard
            feedback.play_clipboard_beep()

        self.status_label.setText("Copied to clipboard!")
