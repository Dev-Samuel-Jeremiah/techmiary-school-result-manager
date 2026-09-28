"""
Techmiary School Result Manager
===============================
By Techmiary Technology Concept - www.techmiary.tech

Desktop software for registering students, entering scores and
printing term results. Works on Windows and Linux.

Run with:   python main.py
"""

import os
import sys
import traceback
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QMainWindow, QPushButton, QStackedWidget,
                               QVBoxLayout, QWidget)

from branding import (APP_VERSION, COMPANY_NAME, COMPANY_URL, COMPANY_WEBSITE,
                      FOOTER_TEXT, PRODUCT_NAME)
from database import Database, data_dir
from pages_admin import ClassesPage, DashboardPage, SettingsPage, StudentsPage, UsersPage
from pages_results import RemarksPage, ResultsPage, ScoresPage
from ui_common import APP_STYLE, confirm, error, info, secondary
from ui_dialogs import ChangePasswordDialog, LoginDialog

APP_TITLE = PRODUCT_NAME


def resource_path(name):
    """Find bundled files both when running from source and from a PyInstaller build."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


class MainWindow(QMainWindow):
    closed = Signal(bool)  # True = user logged out, False = exit the program

    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.logged_out = False
        self.setWindowTitle(f"{APP_TITLE} — {db.get_setting('school_name')}")
        self.resize(1250, 780)

        # Which screens this user may see
        is_admin = user["role"] == "admin"
        is_form_teacher = bool(db.form_classes(user))
        page_classes = [DashboardPage]
        if is_admin:
            page_classes += [StudentsPage, ClassesPage, UsersPage]
        page_classes += [ScoresPage]
        if is_admin or is_form_teacher:
            page_classes += [RemarksPage, ResultsPage]
        if is_admin:
            page_classes += [SettingsPage]

        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFixedWidth(215)
        self.stack = QStackedWidget()
        self.pages = []
        for cls in page_classes:
            page = cls(db, user)
            self.pages.append(page)
            self.stack.addWidget(page)
            QListWidgetItem(cls.title, self.nav)
        self.nav.currentRowChanged.connect(self.switch_page)

        # Top bar
        self.top_info = QLabel()
        self.top_info.setObjectName("topInfo")
        logout = secondary(QPushButton("Log Out"))
        logout.clicked.connect(self.logout)
        top = QHBoxLayout()
        top.setContentsMargins(20, 10, 20, 0)
        top.addWidget(self.top_info)
        top.addStretch()
        top.addWidget(logout)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.addLayout(top)
        right.addWidget(self.stack)

        central = QWidget()
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(self.nav)
        h.addLayout(right)
        self.setCentralWidget(central)

        # Footer (bottom bar): company name and website
        footer = QLabel(f'\u00a9 {COMPANY_NAME} &nbsp;|&nbsp; '
                        f'<a href="{COMPANY_URL}">{COMPANY_WEBSITE}</a> '
                        f'&nbsp;|&nbsp; v{APP_VERSION}')
        footer.setOpenExternalLinks(True)
        footer.setObjectName("footer")
        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().addPermanentWidget(footer, 1)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.build_menu(is_admin)
        self.update_top_bar()
        self.current_index = 0
        self.nav.setCurrentRow(0)
        self.pages[0].refresh()

    # ------------------------------------------------------------------
    def build_menu(self, is_admin):
        bar = self.menuBar()
        file_menu = bar.addMenu("&File")
        if is_admin:
            a = QAction("Back Up Database...", self)
            a.triggered.connect(self.backup)
            file_menu.addAction(a)
            a = QAction("Restore From Backup...", self)
            a.triggered.connect(self.restore)
            file_menu.addAction(a)
            a = QAction("Open Data Folder Location", self)
            a.triggered.connect(lambda: info(self, f"Your data is stored in:\n{data_dir()}"))
            file_menu.addAction(a)
            file_menu.addSeparator()
        a = QAction("Log Out", self)
        a.triggered.connect(self.logout)
        file_menu.addAction(a)
        a = QAction("Exit", self)
        a.triggered.connect(self.close)
        file_menu.addAction(a)

        acct = bar.addMenu("&Account")
        a = QAction("Change My Password...", self)
        a.triggered.connect(lambda: ChangePasswordDialog(self.db, self.user, parent=self).exec()
                            and info(self, "Password changed."))
        acct.addAction(a)

        help_menu = bar.addMenu("&Help")
        a = QAction("About", self)
        a.triggered.connect(lambda: info(
            self, f"<b>{APP_TITLE}</b><br>Version {APP_VERSION}<br><br>"
                  "Register students, enter CA and exam scores, and print term results "
                  "for primary and secondary schools.<br><br>"
                  f"Developed by <b>{COMPANY_NAME}</b><br>"
                  f'<a href="{COMPANY_URL}">{COMPANY_WEBSITE}</a>', "About"))
        help_menu.addAction(a)

    def update_top_bar(self):
        s = self.db.get_settings()
        role = "Administrator" if self.user["role"] == "admin" else "Teacher"
        self.top_info.setText(
            f"<b>{s.get('school_name')}</b> &nbsp;|&nbsp; {s.get('current_session')} "
            f"{s.get('current_term')} &nbsp;|&nbsp; Logged in as {self.user['full_name']} "
            f"({role})")
        self.setWindowTitle(f"{APP_TITLE} — {s.get('school_name')}")

    def switch_page(self, index):
        if index == self.current_index:
            return
        if not self.pages[self.current_index].can_leave():
            self.nav.blockSignals(True)
            self.nav.setCurrentRow(self.current_index)
            self.nav.blockSignals(False)
            return
        self.current_index = index
        self.stack.setCurrentIndex(index)
        try:
            self.pages[index].refresh()
        except Exception as exc:
            error(self, f"Something went wrong while opening this page:\n{exc}")

    # ------------------------------------------------------------------
    def backup(self):
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        path, _ = QFileDialog.getSaveFileName(
            self, "Back up database",
            os.path.join(os.path.expanduser("~"), f"school_backup_{stamp}.db"),
            "Database backup (*.db)")
        if path:
            if not path.lower().endswith(".db"):
                path += ".db"
            try:
                self.db.backup_to(path)
                info(self, f"Backup saved to:\n{path}\n\nKeep a copy on a flash drive or "
                           "online storage.")
            except Exception as exc:
                error(self, f"Backup failed:\n{exc}")

    def restore(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose backup file",
                                              os.path.expanduser("~"),
                                              "Database backup (*.db)")
        if not path:
            return
        if not confirm(self, "Restoring will REPLACE all current data with the backup.\n"
                             "It is wise to make a backup of the current data first.\n\n"
                             "Continue?"):
            return
        try:
            self.db.restore_from(path)
        except Exception as exc:
            return error(self, f"Restore failed:\n{exc}")
        info(self, "Backup restored. Please log in again.")
        self.logout(force=True)

    def logout(self, force=False):
        if not force and not self.pages[self.current_index].can_leave():
            return
        self.logged_out = True
        self.close()

    def closeEvent(self, event):
        if not self.logged_out and not self.pages[self.current_index].can_leave():
            event.ignore()
            return
        event.accept()
        self.closed.emit(self.logged_out)


def excepthook(exc_type, exc, tb):
    """Show unexpected errors instead of silently closing."""
    text = "".join(traceback.format_exception(exc_type, exc, tb))
    try:
        with open(os.path.join(data_dir(), "error.log"), "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now()}]\n{text}")
    except OSError:
        pass
    if QApplication.instance():
        error(None, f"An unexpected error occurred:\n\n{exc}\n\n"
                    f"Details were saved to error.log in:\n{data_dir()}")


def main():
    sys.excepthook = excepthook
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(COMPANY_NAME)
    app.setOrganizationDomain("techmiary.tech")
    app.setStyle("Fusion")  # looks the same on Windows and Linux
    app.setStyleSheet(APP_STYLE)
    icon_file = resource_path("icon.png")
    if os.path.exists(icon_file):
        app.setWindowIcon(QIcon(icon_file))

    db = Database()
    app.setQuitOnLastWindowClosed(False)
    state = {"window": None}

    def show_login():
        login = LoginDialog(db)
        if not login.exec():
            app.quit()
            return
        user = login.user
        if user["must_change"]:
            if not ChangePasswordDialog(db, user, forced=True).exec():
                QTimer.singleShot(0, show_login)
                return
            user = db.query_one("SELECT * FROM users WHERE id=?", (user["id"],))
        window = MainWindow(db, user)
        window.closed.connect(on_window_closed)
        state["window"] = window
        window.show()

    def on_window_closed(logged_out):
        # Wait until the window has fully closed before cleaning up
        QTimer.singleShot(0, lambda: after_close(logged_out))

    def after_close(logged_out):
        old = state["window"]
        state["window"] = None
        if old is not None:
            old.deleteLater()
        if logged_out:
            show_login()
        else:
            app.quit()

    QTimer.singleShot(0, show_login)
    app.exec()
    db.close()

if __name__ == "__main__":
    main()
