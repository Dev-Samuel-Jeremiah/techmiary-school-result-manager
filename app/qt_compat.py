"""
qt_compat.py - lets the same code run on Qt 5 and Qt 6.

* Windows build: PySide2 (Qt 5.15) -> runs on Windows 7, 8, 8.1, 10 and 11.
* Linux build:   PySide6 (Qt 6)    -> modern Linux.

All screens import Qt through "qtpy", which picks whichever binding is installed.
This file fills the few gaps qtpy leaves, and must be imported before the
QApplication is created (main.py does this).
"""

from qtpy import API_NAME, QT5
from qtpy import QtPrintSupport, QtWidgets
from qtpy.QtCore import QCoreApplication, Qt


def _add_exec_alias(cls):
    """Qt 5 bindings call it exec_(); Qt 6 bindings call it exec()."""
    if not hasattr(cls, "exec") and hasattr(cls, "exec_"):
        cls.exec = cls.exec_


for _cls in (QtWidgets.QApplication, QtWidgets.QDialog, QtWidgets.QMenu,
             QtWidgets.QMessageBox, QtPrintSupport.QPrintPreviewDialog,
             QtPrintSupport.QPrintDialog):
    _add_exec_alias(_cls)


def prepare_application():
    """Call this BEFORE QApplication(...) is created."""
    if QT5:
        # Qt 6 does this automatically; Qt 5 needs it for sharp text on
        # high-resolution / scaled screens.
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def qt_description():
    """e.g. 'PySide2 / Qt 5.15.2' - shown in Help > About."""
    try:
        from qtpy import QT_VERSION
    except ImportError:
        QT_VERSION = "?"
    return f"{API_NAME} / Qt {QT_VERSION}"
