"""History tab widget for viewing past transcriptions."""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QTextEdit,
    QSplitter,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .database import get_db, TranscriptionRecord


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


def format_duration(seconds: float) -> str:
    """Format seconds to mm:ss or hh:mm:ss."""
    if seconds is None:
        return "--:--"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    if mins >= 60:
        hours = mins // 60
        mins = mins % 60
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


class HistoryWidget(QWidget):
    """Widget for browsing transcription history."""

    transcription_selected = pyqtSignal(str)  # Emits transcript text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_records: list[TranscriptionRecord] = []
        self.current_offset = 0
        self.page_size = 50
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search transcriptions...")
        self.search_input.returnPressed.connect(self.on_search)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.on_search)
        search_layout.addWidget(search_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_btn)

        layout.addLayout(search_layout)

        # Main content: list + preview
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Transcription list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)

        self.list = QListWidget()
        self.list.setAlternatingRowColors(True)
        self.list.itemClicked.connect(self.on_item_clicked)
        self.list.itemDoubleClicked.connect(self.on_item_double_clicked)
        list_layout.addWidget(self.list)

        # Pagination
        pagination = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        pagination.addWidget(self.prev_btn)

        self.page_label = QLabel("Page 1")
        pagination.addWidget(self.page_label)

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_page)
        pagination.addWidget(self.next_btn)

        pagination.addStretch()

        self.count_label = QLabel("")
        pagination.addWidget(self.count_label)

        list_layout.addLayout(pagination)
        splitter.addWidget(list_widget)

        # Preview area
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_header = QHBoxLayout()
        preview_header.addWidget(QLabel("Preview:"))
        preview_header.addStretch()

        self.meta_label = QLabel("")
        self.meta_label.setStyleSheet("color: #666; font-size: 11px;")
        preview_header.addWidget(self.meta_label)

        preview_layout.addLayout(preview_header)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFont(QFont("Sans", 10))
        preview_layout.addWidget(self.preview)

        # Preview actions
        preview_actions = QHBoxLayout()

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self.copy_selected)
        self.copy_btn.setEnabled(False)
        preview_actions.addWidget(self.copy_btn)

        self.use_btn = QPushButton("Use in Editor")
        self.use_btn.clicked.connect(self.use_selected)
        self.use_btn.setEnabled(False)
        preview_actions.addWidget(self.use_btn)

        preview_actions.addStretch()

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("color: #dc3545;")
        preview_actions.addWidget(self.delete_btn)

        preview_layout.addLayout(preview_actions)
        splitter.addWidget(preview_widget)

        splitter.setSizes([300, 200])
        layout.addWidget(splitter, 1)

        # Storage stats
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #666; font-size: 11px;")
        stats_layout.addWidget(self.stats_label)

        stats_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        stats_layout.addWidget(refresh_btn)

        layout.addLayout(stats_layout)

    def refresh(self):
        """Refresh the transcription list."""
        self.current_offset = 0
        self.load_page()
        self.update_stats()

    def load_page(self):
        """Load current page of transcriptions."""
        search = self.search_input.text().strip() or None
        db = get_db()

        self.current_records = db.get_transcriptions(
            limit=self.page_size,
            offset=self.current_offset,
            search=search,
        )

        total_count = db.get_total_count(search=search)

        self.list.clear()
        for record in self.current_records:
            # Format timestamp
            try:
                dt = datetime.fromisoformat(record.timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = record.timestamp[:16]

            # Format preview text
            preview = record.transcript_text[:60].replace('\n', ' ')
            if len(record.transcript_text) > 60:
                preview += "..."

            # Format duration
            duration = format_duration(record.audio_duration_seconds)

            # Create list item
            item_text = f"{time_str} | {duration} | {record.model}\n{preview}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, record.id)
            self.list.addItem(item)

        # Update pagination
        current_page = (self.current_offset // self.page_size) + 1
        total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"Page {current_page} of {total_pages}")
        self.prev_btn.setEnabled(self.current_offset > 0)
        self.next_btn.setEnabled(self.current_offset + self.page_size < total_count)
        self.count_label.setText(f"{total_count} transcriptions")

        # Clear preview
        self.preview.clear()
        self.meta_label.setText("")
        self.copy_btn.setEnabled(False)
        self.use_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def update_stats(self):
        """Update storage statistics display."""
        db = get_db()
        stats = db.get_storage_stats()

        total_size = format_size(stats["total_size_bytes"])
        db_size = format_size(stats["db_size_bytes"])
        audio_size = format_size(stats["audio_size_bytes"])

        self.stats_label.setText(
            f"Storage: {total_size} total ({db_size} database, {audio_size} audio) | "
            f"{stats['records_with_audio']} with audio"
        )

    def on_search(self):
        """Handle search."""
        self.current_offset = 0
        self.load_page()

    def clear_search(self):
        """Clear search and refresh."""
        self.search_input.clear()
        self.refresh()

    def prev_page(self):
        """Go to previous page."""
        if self.current_offset >= self.page_size:
            self.current_offset -= self.page_size
            self.load_page()

    def next_page(self):
        """Go to next page."""
        self.current_offset += self.page_size
        self.load_page()

    def on_item_clicked(self, item: QListWidgetItem):
        """Handle item click - show preview."""
        record_id = item.data(Qt.ItemDataRole.UserRole)
        db = get_db()
        record = db.get_transcription(record_id)

        if record:
            self.preview.setPlainText(record.transcript_text)

            # Build metadata string
            meta_parts = []
            if record.audio_duration_seconds:
                meta_parts.append(f"Duration: {format_duration(record.audio_duration_seconds)}")
            if record.vad_audio_duration_seconds and record.audio_duration_seconds:
                reduction = (1 - record.vad_audio_duration_seconds / record.audio_duration_seconds) * 100
                meta_parts.append(f"VAD: -{reduction:.0f}%")
            if record.inference_time_ms:
                meta_parts.append(f"Inference: {record.inference_time_ms}ms")
            if record.estimated_cost:
                meta_parts.append(f"Cost: ${record.estimated_cost:.4f}")
            meta_parts.append(f"{record.word_count} words")

            self.meta_label.setText(" | ".join(meta_parts))

            self.copy_btn.setEnabled(True)
            self.use_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)

    def on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double click - use in editor."""
        self.use_selected()

    def get_selected_record(self) -> TranscriptionRecord | None:
        """Get the currently selected record."""
        item = self.list.currentItem()
        if not item:
            return None
        record_id = item.data(Qt.ItemDataRole.UserRole)
        return get_db().get_transcription(record_id)

    def copy_selected(self):
        """Copy selected transcription to clipboard."""
        record = self.get_selected_record()
        if record:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(record.transcript_text)

    def use_selected(self):
        """Emit selected transcription for use in editor."""
        record = self.get_selected_record()
        if record:
            self.transcription_selected.emit(record.transcript_text)

    def delete_selected(self):
        """Delete selected transcription."""
        item = self.list.currentItem()
        if not item:
            return

        record_id = item.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Delete Transcription",
            "Are you sure you want to delete this transcription?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            db = get_db()
            if db.delete_transcription(record_id):
                self.load_page()
                self.update_stats()
