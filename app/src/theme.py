"""Global application stylesheet.

Centralized styles for consistent look and feel across the app.
Individual widgets can still override these with inline setStyleSheet.
"""

APP_STYLESHEET = """
/* ── Global Defaults ─────────────────────────────────────── */

QWidget {
    font-size: 13px;
}

/* ── Checkboxes ──────────────────────────────────────────── */

QCheckBox {
    spacing: 8px;
    padding: 4px 2px;
    color: #333;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 3px;
    border: 2px solid #adb5bd;
    background-color: #fff;
}

QCheckBox::indicator:hover {
    border-color: #6c757d;
}

QCheckBox::indicator:checked {
    background-color: #0d6efd;
    border-color: #0d6efd;
    image: none;
}

QCheckBox::indicator:checked:hover {
    background-color: #0b5ed7;
    border-color: #0b5ed7;
}

QCheckBox::indicator:disabled {
    background-color: #e9ecef;
    border-color: #ced4da;
}

/* ── Radio Buttons ───────────────────────────────────────── */

QRadioButton {
    spacing: 8px;
    padding: 4px 2px;
    color: #333;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #adb5bd;
    background-color: #fff;
}

QRadioButton::indicator:hover {
    border-color: #6c757d;
}

QRadioButton::indicator:checked {
    background-color: #fff;
    border: 5px solid #0d6efd;
}

QRadioButton::indicator:checked:hover {
    border-color: #0b5ed7;
}

/* ── Combo Boxes ─────────────────────────────────────────── */

QComboBox {
    padding: 6px 10px;
    border: 1px solid #ced4da;
    border-radius: 6px;
    background-color: #fff;
    color: #333;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #86b7fe;
}

QComboBox:focus {
    border-color: #0d6efd;
    outline: none;
}

QComboBox::drop-down {
    border: none;
    width: 28px;
    subcontrol-position: right center;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    border: 1px solid #ced4da;
    border-radius: 6px;
    background-color: #fff;
    selection-background-color: #e7f1ff;
    selection-color: #0d6efd;
    padding: 4px;
}

QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    min-height: 24px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #f0f0f0;
}

/* ── Push Buttons (default, non-custom) ──────────────────── */

QPushButton {
    padding: 6px 16px;
    border: 1px solid #ced4da;
    border-radius: 6px;
    background-color: #fff;
    color: #333;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #f0f0f0;
    border-color: #adb5bd;
}

QPushButton:pressed {
    background-color: #e2e6ea;
}

QPushButton:disabled {
    background-color: #e9ecef;
    color: #adb5bd;
    border-color: #dee2e6;
}

/* ── Tabs ────────────────────────────────────────────────── */

QTabWidget::pane {
    border: 1px solid #dee2e6;
    border-radius: 0 0 6px 6px;
    background-color: #fff;
}

QTabBar::tab {
    padding: 8px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    color: #6c757d;
    margin-right: 2px;
}

QTabBar::tab:hover {
    color: #333;
    background-color: #f8f9fa;
}

QTabBar::tab:selected {
    color: #0d6efd;
    border-bottom: 2px solid #0d6efd;
}

/* ── Group Boxes ─────────────────────────────────────────── */

QGroupBox {
    font-weight: bold;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
    color: #495057;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #495057;
}

/* ── Text Inputs ─────────────────────────────────────────── */

QLineEdit {
    padding: 6px 10px;
    border: 1px solid #ced4da;
    border-radius: 6px;
    background-color: #fff;
    color: #333;
    min-height: 20px;
}

QLineEdit:focus {
    border-color: #0d6efd;
}

QTextEdit {
    border: 1px solid #ced4da;
    border-radius: 6px;
    background-color: #fff;
    color: #333;
    padding: 6px;
}

QTextEdit:focus {
    border-color: #0d6efd;
}

/* ── Spin Boxes ──────────────────────────────────────────── */

QSpinBox {
    padding: 6px 10px;
    border: 1px solid #ced4da;
    border-radius: 6px;
    background-color: #fff;
    color: #333;
    min-height: 20px;
}

QSpinBox:focus {
    border-color: #0d6efd;
}

/* ── Scroll Bars ─────────────────────────────────────────── */

QScrollBar:vertical {
    width: 10px;
    background: transparent;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #ced4da;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #adb5bd;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    height: 0;
    background: transparent;
}

QScrollBar:horizontal {
    height: 10px;
    background: transparent;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #ced4da;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #adb5bd;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    width: 0;
    background: transparent;
}

/* ── Tooltips ────────────────────────────────────────────── */

QToolTip {
    background-color: #333;
    color: #fff;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ── Menu Bar ────────────────────────────────────────────── */

QMenuBar {
    background-color: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    padding: 2px 0;
}

QMenuBar::item {
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:hover,
QMenuBar::item:selected {
    background-color: #e9ecef;
}

QMenu {
    background-color: #fff;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #e7f1ff;
    color: #0d6efd;
}

QMenu::separator {
    height: 1px;
    background-color: #dee2e6;
    margin: 4px 8px;
}

/* ── Dialogs ─────────────────────────────────────────────── */

QDialog {
    background-color: #fff;
}

/* ── Message Boxes ───────────────────────────────────────── */

QMessageBox {
    background-color: #fff;
}
"""
