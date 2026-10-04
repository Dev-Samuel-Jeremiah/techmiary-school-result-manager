"""
ui_common.py - Small shared pieces used by every screen:
message boxes, table helpers, the app colour theme and printing.
"""

import os

from qtpy.QtCore import Qt, QUrl, QMarginsF
from qtpy.QtGui import QImage, QPageLayout, QPageSize, QTextDocument
from qtpy.QtPrintSupport import QPrinter, QPrintPreviewDialog
from qtpy.QtWidgets import (QAbstractItemView, QComboBox, QFileDialog, QHeaderView,
                               QMessageBox, QTableWidget, QTableWidgetItem)

from database import SECTIONS, TERMS

# ----------------------------------------------------------------------
# Theme
# ----------------------------------------------------------------------
PRIMARY = "#0b3d91"

APP_STYLE = f"""
QWidget {{ font-size: 10pt; }}
QMainWindow, QDialog {{ background: #f4f6fb; }}
QListWidget#nav {{
    background: {PRIMARY}; color: white; border: none; font-size: 11pt; padding-top: 8px;
}}
QStatusBar {{ background: #e9edf6; border-top: 1px solid #d0d7e6; }}
QLabel#footer {{ color: #555; font-size: 9pt; padding: 2px; }}
QListWidget#nav::item {{ padding: 12px 14px; }}
QListWidget#nav::item:selected {{ background: #ffffff; color: {PRIMARY}; font-weight: bold; }}
QListWidget#nav::item:hover:!selected {{ background: #1a4fa8; }}
QLabel#pageTitle {{ font-size: 16pt; font-weight: bold; color: {PRIMARY}; }}
QLabel#topInfo {{ color: #333; }}
QFrame#card {{ background: white; border: 1px solid #dde3ee; border-radius: 8px; }}
QLabel#cardNumber {{ font-size: 24pt; font-weight: bold; color: {PRIMARY}; }}
QLabel#cardLabel {{ color: #555; }}
QPushButton {{
    background: {PRIMARY}; color: white; border: none; border-radius: 5px;
    padding: 7px 14px;
}}
QPushButton:hover {{ background: #1a4fa8; }}
QPushButton:disabled {{ background: #9aa8c4; }}
QPushButton[secondary="true"] {{ background: #e3e8f2; color: #1b2a45; }}
QPushButton[secondary="true"]:hover {{ background: #d3dbeb; }}
QPushButton[danger="true"] {{ background: #c0392b; }}
QPushButton[danger="true"]:hover {{ background: #a93226; }}
QTableWidget {{
    background: white; gridline-color: #e1e6ef; border: 1px solid #d5dbe7;
    selection-background-color: #cfe0ff; selection-color: black;
}}
QHeaderView::section {{
    background: #e8edf7; padding: 5px; border: none; border-right: 1px solid #d5dbe7;
    font-weight: bold;
}}
QLineEdit, QComboBox, QDateEdit, QSpinBox, QTextEdit, QPlainTextEdit {{
    background: white; border: 1px solid #c5cedf; border-radius: 4px; padding: 4px;
}}
QGroupBox {{
    font-weight: bold; border: 1px solid #d5dbe7; border-radius: 6px; margin-top: 12px;
    background: white; padding-top: 8px;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {PRIMARY}; }}
"""


def secondary(button):
    button.setProperty("secondary", True)
    return button


def danger(button):
    button.setProperty("danger", True)
    return button


# ----------------------------------------------------------------------
# Message helpers
# ----------------------------------------------------------------------
def info(parent, text, title="Information"):
    QMessageBox.information(parent, title, text)


def warn(parent, text, title="Please check"):
    QMessageBox.warning(parent, title, text)


def error(parent, text, title="Error"):
    QMessageBox.critical(parent, title, text)


def confirm(parent, text, title="Confirm"):
    answer = QMessageBox.question(parent, title, text,
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                  QMessageBox.StandardButton.No)
    return answer == QMessageBox.StandardButton.Yes


# ----------------------------------------------------------------------
# Table helpers
# ----------------------------------------------------------------------
def make_table(headers, stretch_column=None, editable=False, multi_select=False):
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection if multi_select
                           else QAbstractItemView.SelectionMode.SingleSelection)
    if not editable:
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    header = table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    if stretch_column is not None:
        header.setSectionResizeMode(stretch_column, QHeaderView.ResizeMode.Stretch)
    return table


def cell(text, data=None, editable=False, align=None):
    item = QTableWidgetItem("" if text is None else str(text))
    if data is not None:
        item.setData(Qt.ItemDataRole.UserRole, data)
    if not editable:
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    if align == "center":
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    return item


def selected_row_data(table, column=0):
    """UserRole data of the first selected row (or None)."""
    rows = sorted({i.row() for i in table.selectedItems()})
    if not rows:
        return None
    item = table.item(rows[0], column)
    return item.data(Qt.ItemDataRole.UserRole) if item else None


def selected_rows_data(table, column=0):
    rows = sorted({i.row() for i in table.selectedItems()})
    result = []
    for r in rows:
        item = table.item(r, column)
        if item:
            result.append(item.data(Qt.ItemDataRole.UserRole))
    return result


# ----------------------------------------------------------------------
# Combo box helpers
# ----------------------------------------------------------------------
def fill_combo(combo, items, empty_label=None, keep_selection=True):
    """items: list of (label, data)."""
    old = combo.currentData() if keep_selection else None
    combo.blockSignals(True)
    combo.clear()
    if empty_label is not None:
        combo.addItem(empty_label, None)
    for label, data in items:
        combo.addItem(label, data)
    if old is not None:
        idx = combo.findData(old)
        if idx >= 0:
            combo.setCurrentIndex(idx)
    combo.blockSignals(False)


def set_combo_data(combo, data):
    idx = combo.findData(data)
    if idx >= 0:
        combo.setCurrentIndex(idx)


def section_combo():
    c = QComboBox()
    for s in SECTIONS:
        c.addItem(s, s)
    return c


def term_combo(db):
    c = QComboBox()
    for t in TERMS:
        c.addItem(t, t)
    set_combo_data(c, db.get_setting("current_term"))
    return c


def session_combo(db):
    c = QComboBox()
    c.setEditable(True)
    c.setMinimumWidth(110)
    for s in db.list_sessions():
        c.addItem(s, s)
    c.setCurrentText(db.get_setting("current_session"))
    return c


# ----------------------------------------------------------------------
# Printing
# ----------------------------------------------------------------------
class ResultDocument(QTextDocument):
    """A text document that can show pictures (logo, student photos)
    kept on disk, looked up by a short name used in the HTML."""

    def __init__(self, html, images=None, css=""):
        super().__init__()
        self._images = {}
        for key, path in (images or {}).items():
            if path and os.path.exists(path):
                img = QImage(path)
                if not img.isNull():
                    self._images[key] = img
        if css:
            self.setDefaultStyleSheet(css)
        self.setHtml(html)

    def loadResource(self, resource_type, name):
        key = name.toString() if isinstance(name, QUrl) else str(name)
        if key in self._images:
            return self._images[key]
        return super().loadResource(resource_type, name)


def make_printer(landscape=False, pdf_path=None):
    """A4 printer with 10 mm margins. Works on Qt 5 (Windows 7/8 build) and Qt 6."""
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    orientation = (QPageLayout.Orientation.Landscape if landscape
                   else QPageLayout.Orientation.Portrait)
    layout = QPageLayout(QPageSize(QPageSize.PageSizeId.A4), orientation,
                         QMarginsF(10, 10, 10, 10), QPageLayout.Unit.Millimeter)
    try:
        # One call that sets paper size, orientation and margins (Qt 5.3+ and Qt 6)
        ok = printer.setPageLayout(layout)
    except (TypeError, AttributeError):
        ok = False
    if ok is False:
        # Fallback: set each part separately
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(orientation)
        try:
            printer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Unit.Millimeter)
        except TypeError:
            # Qt 5 form of the same call
            printer.setPageMargins(10, 10, 10, 10, QPrinter.Unit.Millimeter)
    if pdf_path:
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(pdf_path)
    return printer


def print_preview(parent, document, landscape=False, title="Print Preview"):
    printer = make_printer(landscape)
    dialog = QPrintPreviewDialog(printer, parent)
    dialog.setWindowTitle(title)
    dialog.resize(1000, 800)
    dialog.paintRequested.connect(lambda p: document.print_(p))
    dialog.exec()


def save_pdf(parent, document, suggested_name, landscape=False):
    path, _ = QFileDialog.getSaveFileName(
        parent, "Save as PDF", os.path.join(os.path.expanduser("~"), suggested_name),
        "PDF files (*.pdf)")
    if not path:
        return None
    if not path.lower().endswith(".pdf"):
        path += ".pdf"
    document.print_(make_printer(landscape, path))
    return path
