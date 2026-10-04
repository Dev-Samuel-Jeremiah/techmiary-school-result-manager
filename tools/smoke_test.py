"""
smoke_test.py - quick automatic check that the program really works with the
Qt version it is being built with. The build scripts run it before packaging,
so a broken build stops with an error instead of reaching users.

It uses a throw-away data folder, opens every screen and pop-up form without
showing them, fills in sample data, and prints result sheets to a PDF.

Run by hand:   python tools/smoke_test.py
"""
import os
import sys
import tempfile
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))

# Never touch real school data, and don't open real windows
TMP = tempfile.mkdtemp(prefix="srm_smoke_")
os.environ["APPDATA"] = TMP
os.environ["XDG_DATA_HOME"] = TMP
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

steps_ok = 0


def step(name, func):
    global steps_ok
    try:
        func()
        steps_ok += 1
        print(f"  OK   {name}")
    except Exception:
        print(f"  FAIL {name}")
        traceback.print_exc()
        sys.exit(1)


import qt_compat  # noqa: E402
from qtpy.QtWidgets import QApplication  # noqa: E402

print(f"Smoke test using {qt_compat.qt_description()}, Python {sys.version.split()[0]}")
qt_compat.prepare_application()
app = QApplication(sys.argv)

import main as app_main  # noqa: E402
from database import Database, data_dir  # noqa: E402
from results import SHEET_CSS, broadsheet_html, build_results_html  # noqa: E402
from ui_common import APP_STYLE, ResultDocument, make_printer  # noqa: E402
import ui_dialogs  # noqa: E402

app.setStyleSheet(APP_STYLE)
db = Database()
state = {}


def sample_data():
    assert data_dir().startswith(TMP), "test is not using the temporary folder"
    admin = db.authenticate("admin", "admin123")
    assert admin, "default admin login failed"
    state["admin"] = admin
    class_id = db.add_class("JSS 1A", "Secondary")
    subjects = db.list_subjects("Secondary")[:3]
    assert subjects, "no default subjects"
    for sub in subjects:
        db.add_class_subject(class_id, sub["id"])
    settings = db.get_settings()
    session, term = settings.get("current_session"), settings.get("current_term")
    for i, (surname, first) in enumerate([("Musa", "Aisha"), ("Okafor", "John"),
                                          ("Danjuma", "Grace")]):
        data = {f: "" for f in Database.STUDENT_FIELDS}
        data.update(admission_no=f"2026/{i + 1:03d}", surname=surname, first_name=first,
                    gender="Female" if i != 1 else "Male", class_id=class_id,
                    status="Active")
        sid = db.save_student(data)
        for j, sub in enumerate(subjects):
            db.save_score(sid, class_id, sub["id"], session, term,
                          10 + i, 12 + j, 40 + i * 5, admin["id"])
    db.commit()
    state.update(class_id=class_id, session=session, term=term)


def dialogs():
    admin = state["admin"]
    ui_dialogs.LoginDialog(db)
    ui_dialogs.ChangePasswordDialog(db, admin, forced=True)
    ui_dialogs.StudentDialog(db)
    ui_dialogs.UserDialog(db)
    klass = db.get_class(state["class_id"])
    ui_dialogs.ClassDialog(db, klass)
    ui_dialogs.PickSubjectsDialog(db, klass)
    ui_dialogs.PickTeacherDialog(db)
    ui_dialogs.SubjectListDialog(db)


def main_window():
    win = app_main.MainWindow(db, state["admin"])
    for page in win.pages:
        page.refresh()
        app.processEvents()
    win.logged_out = True
    win.close()


def printing():
    html, data = build_results_html(db, state["class_id"], state["session"], state["term"])
    assert len(data["students"]) == 3, "expected 3 students in results"
    doc = ResultDocument(html, {}, SHEET_CSS)
    pdf = os.path.join(TMP, "results.pdf")
    doc.print_(make_printer(pdf_path=pdf))
    assert os.path.getsize(pdf) > 1000, "result PDF is empty"
    sheet = ResultDocument(broadsheet_html(db, state["class_id"], state["session"],
                                           state["term"]), {}, SHEET_CSS)
    pdf2 = os.path.join(TMP, "broadsheet.pdf")
    sheet.print_(make_printer(landscape=True, pdf_path=pdf2))
    assert os.path.getsize(pdf2) > 1000, "broadsheet PDF is empty"


def preview_window():
    from qtpy.QtPrintSupport import QPrintPreviewDialog
    for landscape in (False, True):
        dialog = QPrintPreviewDialog(make_printer(landscape), None)
        dialog.paintRequested.connect(lambda p: None)
        dialog.close()


def backup():
    path = os.path.join(TMP, "backup.db")
    db.backup_to(path)
    assert os.path.getsize(path) > 0


step("sample data", sample_data)
step("pop-up forms", dialogs)
step("main window and every screen", main_window)
step("print result sheets and broadsheet to PDF", printing)
step("print preview window", preview_window)
step("backup", backup)
db.close()
print(f"Smoke test passed ({steps_ok} checks).")
