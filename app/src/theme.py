"""Global application stylesheet.

Centralized styles for consistent look and feel across the app.
Only styles widgets that benefit from global consistency.
Individual widgets can still override these with inline setStyleSheet.

IMPORTANT: Avoid styling QPushButton, QWidget, or other broad selectors
globally — too many custom buttons rely on specific inline styles.
"""

APP_STYLESHEET = """
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
    background-color: #198754;
    border-color: #198754;
}

QCheckBox::indicator:checked:hover {
    background-color: #146c43;
    border-color: #146c43;
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
    border: 5px solid #198754;
}

QRadioButton::indicator:checked:hover {
    border-color: #146c43;
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
"""
