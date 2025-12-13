"""Markdown rendering widget for PyQt6."""

import markdown
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QTextBrowser, QStackedWidget
from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal


# CSS styles for rendered markdown
MARKDOWN_CSS = """
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #333;
    padding: 8px;
}
h1, h2, h3, h4, h5, h6 {
    margin-top: 1em;
    margin-bottom: 0.5em;
    font-weight: 600;
    line-height: 1.25;
}
h1 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
h2 { font-size: 1.3em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
h3 { font-size: 1.15em; }
p { margin: 0.5em 0; }
ul, ol { margin: 0.5em 0; padding-left: 2em; }
li { margin: 0.25em 0; }
code {
    background-color: #f6f8fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9em;
}
pre {
    background-color: #f6f8fa;
    padding: 1em;
    border-radius: 6px;
    overflow-x: auto;
}
pre code {
    background: none;
    padding: 0;
}
blockquote {
    border-left: 4px solid #dfe2e5;
    padding-left: 1em;
    margin: 0.5em 0;
    color: #6a737d;
}
"""


class MarkdownTextWidget(QWidget):
    """Widget that displays markdown with toggle between rendered and source view."""

    textChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._markdown_text = ""
        self._is_rendered_view = True
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Toggle button row
        toggle_row = QHBoxLayout()
        toggle_row.setContentsMargins(0, 0, 0, 0)

        self.toggle_btn = QPushButton("View Source")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setMaximumWidth(100)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:checked {
                background-color: #007bff;
                color: white;
                border-color: #007bff;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
            QPushButton:checked:hover {
                background-color: #0056b3;
            }
        """)
        self.toggle_btn.clicked.connect(self._on_toggle)
        toggle_row.addWidget(self.toggle_btn)
        toggle_row.addStretch()

        layout.addLayout(toggle_row)

        # Stacked widget for rendered/source views
        self.stack = QStackedWidget()

        # Rendered view (QTextBrowser for HTML)
        self.rendered_view = QTextBrowser()
        self.rendered_view.setOpenExternalLinks(True)
        self.rendered_view.setStyleSheet("QTextBrowser { border: 1px solid #ced4da; border-radius: 4px; }")
        self.stack.addWidget(self.rendered_view)

        # Source view (QTextEdit for editing)
        self.source_view = QTextEdit()
        self.source_view.setFont(QFont("Monospace", 11))
        self.source_view.setStyleSheet("QTextEdit { border: 1px solid #ced4da; border-radius: 4px; }")
        self.source_view.textChanged.connect(self._on_source_changed)
        self.stack.addWidget(self.source_view)

        layout.addWidget(self.stack, 1)

    def _on_toggle(self, checked: bool):
        """Toggle between rendered and source view."""
        if checked:
            # Switch to source view
            self.toggle_btn.setText("View Rendered")
            self._markdown_text = self.source_view.toPlainText()
            self.stack.setCurrentWidget(self.source_view)
            self._is_rendered_view = False
        else:
            # Switch to rendered view
            self.toggle_btn.setText("View Source")
            self._markdown_text = self.source_view.toPlainText()
            self._update_rendered()
            self.stack.setCurrentWidget(self.rendered_view)
            self._is_rendered_view = True

    def _on_source_changed(self):
        """Handle source text changes."""
        self._markdown_text = self.source_view.toPlainText()
        self.textChanged.emit()

    def _update_rendered(self):
        """Update the rendered HTML view."""
        if not self._markdown_text:
            self.rendered_view.setHtml("")
            return

        # Convert markdown to HTML
        html = markdown.markdown(
            self._markdown_text,
            extensions=['fenced_code', 'tables', 'nl2br']
        )

        # Wrap with CSS
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>{MARKDOWN_CSS}</style>
        </head>
        <body>{html}</body>
        </html>
        """
        self.rendered_view.setHtml(full_html)

    def setMarkdown(self, text: str):
        """Set the markdown text content."""
        self._markdown_text = text
        self.source_view.setPlainText(text)
        if self._is_rendered_view:
            self._update_rendered()

    def setPlainText(self, text: str):
        """Alias for setMarkdown for compatibility."""
        self.setMarkdown(text)

    def toPlainText(self) -> str:
        """Get the markdown text content."""
        if self._is_rendered_view:
            return self._markdown_text
        return self.source_view.toPlainText()

    def clear(self):
        """Clear the content."""
        self._markdown_text = ""
        self.source_view.clear()
        self.rendered_view.clear()

    def setPlaceholderText(self, text: str):
        """Set placeholder text for the source view."""
        self.source_view.setPlaceholderText(text)

    def setFont(self, font: QFont):
        """Set font for the source view."""
        self.source_view.setFont(font)
