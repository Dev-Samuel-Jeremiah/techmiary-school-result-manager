"""
pages_admin.py - Screens mainly used by the administrator:
Dashboard, Students, Classes & Subjects, Staff Accounts and Settings.
"""

import os
import shutil

from qtpy.QtCore import Qt
from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import (QComboBox, QFileDialog, QFormLayout, QFrame, QGridLayout,
                               QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                               QPushButton, QSplitter, QTabWidget,
                               QVBoxLayout, QWidget)

from database import DEFAULT_GRADES, SECTIONS, TERMS, data_dir
from results import fmt
from ui_common import (cell, confirm, danger, fill_combo, info, make_table, secondary,
                       selected_row_data, selected_rows_data, warn)
from ui_dialogs import (ClassDialog, PickSubjectsDialog, PickTeacherDialog, StudentDialog,
                        SubjectListDialog, UserDialog)


class Page(QWidget):
    """Base for every screen: a title at the top and a refresh() hook."""

    title = ""

    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(20, 16, 20, 16)
        heading = QLabel(self.title)
        heading.setObjectName("pageTitle")
        self.layout_.addWidget(heading)

    @property
    def is_admin(self):
        return self.user["role"] == "admin"

    def refresh(self):
        pass

    def can_leave(self):
        """Return False to stop the user leaving (e.g. unsaved scores)."""
        return True


# ======================================================================
# Dashboard
# ======================================================================
class DashboardPage(Page):
    title = "Dashboard"

    def __init__(self, db, user):
        super().__init__(db, user)
        self.welcome = QLabel()
        self.welcome.setStyleSheet("font-size: 12pt;")
        self.layout_.addWidget(self.welcome)

        self.cards = {}
        grid = QGridLayout()
        for i, (key, label) in enumerate([("students", "Active Students"),
                                          ("classes", "Classes"),
                                          ("teachers", "Teachers"),
                                          ("subjects", "Subjects")]):
            card = QFrame()
            card.setObjectName("card")
            v = QVBoxLayout(card)
            num = QLabel("0")
            num.setObjectName("cardNumber")
            lab = QLabel(label)
            lab.setObjectName("cardLabel")
            v.addWidget(num)
            v.addWidget(lab)
            self.cards[key] = num
            grid.addWidget(card, 0, i)
        self.layout_.addLayout(grid)

        self.assign_box = QGroupBox("My Subjects and Classes")
        self.assign_label = QLabel()
        self.assign_label.setWordWrap(True)
        self.assign_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        QVBoxLayout(self.assign_box).addWidget(self.assign_label)
        self.layout_.addWidget(self.assign_box)

        guide = QGroupBox("How to use this software")
        g = QLabel()
        g.setWordWrap(True)
        if self.is_admin:
            g.setText(
                "<ol>"
                "<li><b>Settings</b> &ndash; enter your school name, address, logo, the current "
                "session and term, and check the grading scale.</li>"
                "<li><b>Staff Accounts</b> &ndash; create an account for each teacher.</li>"
                "<li><b>Classes &amp; Subjects</b> &ndash; create classes, choose each class's "
                "subjects and assign a teacher to every subject and a class teacher to every "
                "class.</li>"
                "<li><b>Students</b> &ndash; register students into their classes.</li>"
                "<li><b>Enter Scores</b> &ndash; teachers log in and type CA and exam scores.</li>"
                "<li><b>Remarks &amp; Attendance</b> &ndash; class teachers add attendance and "
                "comments; you add the principal's comment.</li>"
                "<li><b>Results</b> &ndash; preview, print or save result sheets as PDF.</li>"
                "</ol>"
                "Tip: use <b>File &gt; Back Up Database</b> regularly and keep the copy on a "
                "flash drive.")
        else:
            g.setText(
                "<ol>"
                "<li>Open <b>Enter Scores</b>, pick one of your class/subject pairs and type "
                "each student's CA and exam scores. Press <b>Save Scores</b>.</li>"
                "<li>If you are a class teacher, use <b>Remarks &amp; Attendance</b> to add "
                "days present and your comment for each student.</li>"
                "<li>Class teachers can print their class's results under <b>Results</b>.</li>"
                "</ol>")
        QVBoxLayout(guide).addWidget(g)
        self.layout_.addWidget(guide)
        self.layout_.addStretch()

    def refresh(self):
        s = self.db.get_settings()
        self.welcome.setText(f"Welcome, <b>{self.user['full_name']}</b>. "
                             f"Current session: <b>{s.get('current_session')}</b> &nbsp; "
                             f"Term: <b>{s.get('current_term')}</b>")
        for k, v in self.db.stats().items():
            self.cards[k].setText(str(v))
        rows = self.db.teacher_assignments(self.user) if not self.is_admin else []
        forms = self.db.form_classes(self.user) if not self.is_admin else []
        if self.is_admin:
            self.assign_box.hide()
        else:
            text = "<b>Subjects I teach:</b> " + (
                ", ".join(f"{r['subject']} ({r['class_name']})" for r in rows)
                or "None yet &ndash; ask the administrator to assign you.")
            if forms:
                text += "<br><b>Class teacher of:</b> " + ", ".join(c["name"] for c in forms)
            self.assign_label.setText(text)


# ======================================================================
# Students
# ======================================================================
class StudentsPage(Page):
    title = "Students"

    def __init__(self, db, user):
        super().__init__(db, user)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name or admission number...")
        self.search.textChanged.connect(self.refresh)
        self.class_filter = QComboBox()
        self.class_filter.currentIndexChanged.connect(self.refresh)
        self.status_filter = QComboBox()
        for s in ["Active", "Graduated", "Left", "Suspended", "All"]:
            self.status_filter.addItem(s, None if s == "All" else s)
        self.status_filter.currentIndexChanged.connect(self.refresh)

        bar = QHBoxLayout()
        bar.addWidget(self.search, 2)
        bar.addWidget(QLabel("Class:"))
        bar.addWidget(self.class_filter, 1)
        bar.addWidget(QLabel("Status:"))
        bar.addWidget(self.status_filter)
        self.layout_.addLayout(bar)

        self.table = make_table(["Adm. No", "Surname", "First Name", "Other Name", "Gender",
                                 "Class", "Guardian", "Guardian Phone", "Status"],
                                stretch_column=6, multi_select=True)
        self.table.doubleClicked.connect(self.edit)
        self.layout_.addWidget(self.table)

        self.count = QLabel()
        add = QPushButton("+ Register Student")
        add.clicked.connect(self.add)
        edit = secondary(QPushButton("Edit"))
        edit.clicked.connect(self.edit)
        move = secondary(QPushButton("Move / Promote Selected"))
        move.clicked.connect(self.move)
        status = secondary(QPushButton("Change Status"))
        status.clicked.connect(self.change_status)
        delete = danger(QPushButton("Delete"))
        delete.clicked.connect(self.delete)

        buttons = QHBoxLayout()
        buttons.addWidget(self.count)
        buttons.addStretch()
        for b in (add, edit, move, status, delete):
            buttons.addWidget(b)
        self.layout_.addLayout(buttons)

    def refresh(self):
        fill_combo(self.class_filter, [(c["name"], c["id"]) for c in self.db.list_classes()],
                   empty_label="All classes")
        students = self.db.list_students(class_id=self.class_filter.currentData(),
                                         search=self.search.text(),
                                         status=self.status_filter.currentData())
        self.table.setRowCount(0)
        for s in students:
            r = self.table.rowCount()
            self.table.insertRow(r)
            vals = [s["admission_no"], s["surname"], s["first_name"], s["other_name"],
                    s["gender"], s["class_name"] or "-", s["guardian_name"],
                    s["guardian_phone"], s["status"]]
            for c, v in enumerate(vals):
                self.table.setItem(r, c, cell(v, s["id"] if c == 0 else None))
        self.count.setText(f"{len(students)} student(s)")

    def add(self):
        if not self.db.list_classes():
            return warn(self, "Create at least one class first (Classes & Subjects).")
        if StudentDialog(self.db, parent=self).exec():
            self.refresh()

    def edit(self, *_):
        sid = selected_row_data(self.table)
        if not sid:
            return info(self, "Select a student first.")
        if StudentDialog(self.db, self.db.get_student(sid), parent=self).exec():
            self.refresh()

    def move(self):
        ids = selected_rows_data(self.table)
        if not ids:
            return info(self, "Select one or more students (hold Ctrl or Shift to select many).")
        classes = self.db.list_classes()
        names = [c["name"] for c in classes]
        if not names:
            return
        name, ok = QInputDialog.getItem(self, "Move students",
                                        f"Move {len(ids)} student(s) to which class?",
                                        names, 0, False)
        if ok:
            cid = classes[names.index(name)]["id"]
            for sid in ids:
                self.db.execute("UPDATE students SET class_id=? WHERE id=?", (cid, sid))
            self.refresh()
            info(self, f"{len(ids)} student(s) moved to {name}. Their old results are kept.")

    def change_status(self):
        ids = selected_rows_data(self.table)
        if not ids:
            return info(self, "Select one or more students.")
        options = ["Active", "Graduated", "Left", "Suspended"]
        status, ok = QInputDialog.getItem(self, "Change status",
                                          f"New status for {len(ids)} student(s):",
                                          options, 0, False)
        if ok:
            for sid in ids:
                self.db.execute("UPDATE students SET status=? WHERE id=?", (status, sid))
            self.refresh()

    def delete(self):
        ids = selected_rows_data(self.table)
        if not ids:
            return info(self, "Select a student first.")
        if confirm(self, f"Permanently delete {len(ids)} student(s) and ALL their scores?\n\n"
                         "Tip: to keep their records, use 'Change Status' instead "
                         "(e.g. Left or Graduated)."):
            for sid in ids:
                self.db.delete_student(sid)
            self.refresh()


# ======================================================================
# Classes & subjects
# ======================================================================
class ClassesPage(Page):
    title = "Classes & Subjects"

    def __init__(self, db, user):
        super().__init__(db, user)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: classes
        left = QGroupBox("Classes")
        lv = QVBoxLayout(left)
        self.classes = make_table(["Class", "Section", "Class Teacher", "Students"],
                                  stretch_column=2)
        self.classes.itemSelectionChanged.connect(self.load_subjects)
        self.classes.doubleClicked.connect(self.edit_class)
        lv.addWidget(self.classes)
        row = QHBoxLayout()
        b = QPushButton("+ New Class")
        b.clicked.connect(self.add_class)
        row.addWidget(b)
        b = secondary(QPushButton("Edit"))
        b.clicked.connect(self.edit_class)
        row.addWidget(b)
        b = danger(QPushButton("Delete"))
        b.clicked.connect(self.delete_class)
        row.addWidget(b)
        lv.addLayout(row)

        # Right: subjects of the selected class
        right = QGroupBox("Subjects offered by the selected class")
        rv = QVBoxLayout(right)
        self.subjects = make_table(["Subject", "Subject Teacher"], stretch_column=1,
                                   multi_select=True)
        self.subjects.doubleClicked.connect(self.set_teacher)
        rv.addWidget(self.subjects)
        row = QHBoxLayout()
        b = QPushButton("+ Add Subjects")
        b.clicked.connect(self.add_subjects)
        row.addWidget(b)
        b = secondary(QPushButton("Set Teacher"))
        b.clicked.connect(self.set_teacher)
        row.addWidget(b)
        b = danger(QPushButton("Remove"))
        b.clicked.connect(self.remove_subjects)
        row.addWidget(b)
        row.addStretch()
        b = secondary(QPushButton("Subject List..."))
        b.clicked.connect(self.subject_list)
        row.addWidget(b)
        rv.addLayout(row)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([450, 550])
        self.layout_.addWidget(splitter)

    def refresh(self):
        current = selected_row_data(self.classes)
        self.classes.setRowCount(0)
        for c in self.db.list_classes():
            r = self.classes.rowCount()
            self.classes.insertRow(r)
            for col, v in enumerate([c["name"], c["section"], c["form_teacher"] or "-",
                                     c["student_count"]]):
                self.classes.setItem(r, col, cell(v, c["id"] if col == 0 else None))
            if c["id"] == current:
                self.classes.selectRow(r)
        if self.classes.rowCount() and not self.classes.selectedItems():
            self.classes.selectRow(0)
        self.load_subjects()

    def current_class(self):
        cid = selected_row_data(self.classes)
        return self.db.get_class(cid) if cid else None

    def load_subjects(self):
        self.subjects.setRowCount(0)
        klass = self.current_class()
        if not klass:
            return
        for cs in self.db.class_subjects(klass["id"]):
            r = self.subjects.rowCount()
            self.subjects.insertRow(r)
            self.subjects.setItem(r, 0, cell(cs["subject"], cs["id"]))
            self.subjects.setItem(r, 1, cell(cs["teacher"] or "— not assigned —", cs["teacher_id"]))

    def add_class(self):
        if ClassDialog(self.db, parent=self).exec():
            self.refresh()

    def edit_class(self, *_):
        klass = self.current_class()
        if not klass:
            return info(self, "Select a class first.")
        if ClassDialog(self.db, klass, parent=self).exec():
            self.refresh()

    def delete_class(self):
        klass = self.current_class()
        if not klass:
            return
        n = self.db.query_one("SELECT COUNT(*) AS n FROM students WHERE class_id=?",
                              (klass["id"],))["n"]
        if n:
            return warn(self, f"{klass['name']} still has {n} student(s). Move them to another "
                              "class first (Students > Move / Promote).")
        if confirm(self, f"Delete class {klass['name']}? Scores recorded under this class "
                         "will also be deleted."):
            self.db.delete_class(klass["id"])
            self.refresh()

    def add_subjects(self):
        klass = self.current_class()
        if not klass:
            return info(self, "Select a class first.")
        dlg = PickSubjectsDialog(self.db, klass, self)
        if dlg.exec():
            for sid in dlg.chosen():
                self.db.add_class_subject(klass["id"], sid)
            self.load_subjects()

    def set_teacher(self, *_):
        ids = selected_rows_data(self.subjects)
        if not ids:
            return info(self, "Select one or more subjects on the right first.")
        row = sorted({i.row() for i in self.subjects.selectedItems()})[0]
        current = self.subjects.item(row, 1).data(Qt.ItemDataRole.UserRole)
        dlg = PickTeacherDialog(self.db, current, "Subject teacher", self)
        if dlg.exec():
            for cs_id in ids:
                self.db.set_class_subject_teacher(cs_id, dlg.teacher_id())
            self.load_subjects()

    def remove_subjects(self):
        ids = selected_rows_data(self.subjects)
        if not ids:
            return
        if confirm(self, f"Remove {len(ids)} subject(s) from this class?\n"
                         "Scores already entered are kept, but the subject will no longer "
                         "appear for score entry."):
            for cs_id in ids:
                self.db.remove_class_subject(cs_id)
            self.load_subjects()

    def subject_list(self):
        SubjectListDialog(self.db, self).exec()
        self.load_subjects()


# ======================================================================
# Staff accounts
# ======================================================================
class UsersPage(Page):
    title = "Staff Accounts"

    def __init__(self, db, user):
        super().__init__(db, user)
        self.table = make_table(["Full Name", "Username", "Role", "Phone", "Status",
                                 "Subjects Assigned", "Class Teacher Of"], stretch_column=5)
        self.table.doubleClicked.connect(self.edit)
        self.layout_.addWidget(self.table)

        row = QHBoxLayout()
        row.addStretch()
        b = QPushButton("+ New Staff Account")
        b.clicked.connect(self.add)
        row.addWidget(b)
        b = secondary(QPushButton("Edit"))
        b.clicked.connect(self.edit)
        row.addWidget(b)
        b = secondary(QPushButton("Reset Password"))
        b.clicked.connect(self.reset_password)
        row.addWidget(b)
        b = danger(QPushButton("Delete"))
        b.clicked.connect(self.delete)
        row.addWidget(b)
        self.layout_.addLayout(row)

    def refresh(self):
        self.table.setRowCount(0)
        for u in self.db.list_users():
            subjects = self.db.query(
                "SELECT s.name || ' (' || c.name || ')' AS x FROM class_subjects cs "
                "JOIN subjects s ON s.id=cs.subject_id JOIN classes c ON c.id=cs.class_id "
                "WHERE cs.teacher_id=? ORDER BY c.name", (u["id"],))
            forms = self.db.query("SELECT name FROM classes WHERE form_teacher_id=?", (u["id"],))
            r = self.table.rowCount()
            self.table.insertRow(r)
            vals = [u["full_name"], u["username"],
                    "Administrator" if u["role"] == "admin" else "Teacher",
                    u["phone"], "Active" if u["active"] else "Disabled",
                    ", ".join(x["x"] for x in subjects) or "-",
                    ", ".join(x["name"] for x in forms) or "-"]
            for c, v in enumerate(vals):
                self.table.setItem(r, c, cell(v, u["id"] if c == 0 else None))

    def selected_user(self):
        uid = selected_row_data(self.table)
        return self.db.query_one("SELECT * FROM users WHERE id=?", (uid,)) if uid else None

    def add(self):
        if UserDialog(self.db, parent=self).exec():
            self.refresh()

    def edit(self, *_):
        u = self.selected_user()
        if not u:
            return info(self, "Select a staff account first.")
        if UserDialog(self.db, u, parent=self).exec():
            self.refresh()

    def reset_password(self):
        u = self.selected_user()
        if not u:
            return info(self, "Select a staff account first.")
        pw, ok = QInputDialog.getText(self, "Reset password",
                                      f"New temporary password for {u['full_name']}:",
                                      QLineEdit.EchoMode.Normal)
        if ok:
            if len(pw) < 6:
                return warn(self, "Password must be at least 6 characters.")
            self.db.set_password(u["id"], pw, must_change=True)
            info(self, f"Password reset. {u['full_name']} will be asked to change it at "
                       "next login.")

    def delete(self):
        u = self.selected_user()
        if not u:
            return
        if u["id"] == self.user["id"]:
            return warn(self, "You cannot delete your own account.")
        if u["role"] == "admin" and self.db.count_admins() <= 1:
            return warn(self, "You cannot delete the only administrator.")
        if confirm(self, f"Delete the account of {u['full_name']}?\n\nScores they entered "
                         "are kept. Their subjects will show as 'not assigned'.\n"
                         "(To only block login, use Edit and untick 'active'.)"):
            self.db.delete_user(u["id"])
            self.refresh()


# ======================================================================
# Settings
# ======================================================================
class SettingsPage(Page):
    title = "Settings"

    def __init__(self, db, user):
        super().__init__(db, user)
        tabs = QTabWidget()

        # --- School info -------------------------------------------------
        school = QWidget()
        form = QFormLayout(school)
        self.fields = {}
        for key, label in [("school_name", "School name"), ("school_address", "Address"),
                           ("school_motto", "Motto"), ("school_phone", "Phone"),
                           ("school_email", "Email"),
                           ("principal_name", "Principal's name (Secondary)"),
                           ("head_teacher_name", "Head teacher's name (Primary)")]:
            w = QLineEdit()
            self.fields[key] = w
            form.addRow(label + ":", w)

        self.logo_preview = QLabel("No logo")
        self.logo_preview.setFixedSize(100, 100)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setStyleSheet("border: 1px dashed #999; background: white;")
        self.logo_path = ""
        logo_btn = secondary(QPushButton("Choose Logo..."))
        logo_btn.clicked.connect(self.choose_logo)
        logo_clear = secondary(QPushButton("Remove"))
        logo_clear.clicked.connect(lambda: self.set_logo(""))
        lrow = QHBoxLayout()
        lrow.addWidget(self.logo_preview)
        lrow.addWidget(logo_btn)
        lrow.addWidget(logo_clear)
        lrow.addStretch()
        form.addRow("School logo:", lrow)
        tabs.addTab(school, "School Information")

        # --- Session / term --------------------------------------------
        term_tab = QWidget()
        tform = QFormLayout(term_tab)
        self.session = QLineEdit()
        self.session.setPlaceholderText("e.g. 2026/2027")
        self.term = QComboBox()
        self.term.addItems(TERMS)
        self.next_term = QLineEdit()
        self.next_term.setPlaceholderText("e.g. Monday, 12th January 2027")
        self.days_opened = QLineEdit()
        self.days_opened.setPlaceholderText("Number of days school opened this term")
        self.ca1 = QLineEdit()
        self.ca2 = QLineEdit()
        self.exam = QLineEdit()
        tform.addRow("Current session:", self.session)
        tform.addRow("Current term:", self.term)
        tform.addRow("Next term begins:", self.next_term)
        tform.addRow("Times school opened:", self.days_opened)
        tform.addRow(QLabel("<b>Maximum scores</b> (must add up to 100)"))
        tform.addRow("1st C.A.:", self.ca1)
        tform.addRow("2nd C.A.:", self.ca2)
        tform.addRow("Examination:", self.exam)
        tabs.addTab(term_tab, "Session, Term & Scores")

        # --- Grading ----------------------------------------------------
        grading = QWidget()
        gv = QVBoxLayout(grading)
        gv.addWidget(QLabel("Edit the grade bands for each section. Scores are out of 100."))
        self.grade_tables = {}
        ghl = QHBoxLayout()
        for section in SECTIONS:
            box = QGroupBox(section)
            bv = QVBoxLayout(box)
            t = make_table(["From", "To", "Grade", "Remark"], stretch_column=3, editable=True)
            self.grade_tables[section] = t
            bv.addWidget(t)
            brow = QHBoxLayout()
            add = secondary(QPushButton("Add Row"))
            add.clicked.connect(lambda _=False, t=t: self.add_grade_row(t))
            rem = secondary(QPushButton("Remove Row"))
            rem.clicked.connect(lambda _=False, t=t: t.removeRow(t.currentRow())
                                if t.currentRow() >= 0 else None)
            reset = secondary(QPushButton("Restore Default"))
            reset.clicked.connect(lambda _=False, s=section: self.load_grades(s, default=True))
            brow.addWidget(add)
            brow.addWidget(rem)
            brow.addWidget(reset)
            bv.addLayout(brow)
            ghl.addWidget(box)
        gv.addLayout(ghl)
        tabs.addTab(grading, "Grading")

        self.layout_.addWidget(tabs)
        save = QPushButton("Save Settings")
        save.clicked.connect(self.save)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(save)
        self.layout_.addLayout(row)

    # ----------------------------------------------------------------
    def refresh(self):
        s = self.db.get_settings()
        for key, w in self.fields.items():
            w.setText(s.get(key, ""))
        self.set_logo(s.get("logo_path", ""))
        self.session.setText(s.get("current_session", ""))
        self.term.setCurrentText(s.get("current_term", TERMS[0]))
        self.next_term.setText(s.get("next_term_begins", ""))
        self.days_opened.setText(s.get("days_school_opened", ""))
        self.ca1.setText(s.get("ca1_max", "20"))
        self.ca2.setText(s.get("ca2_max", "20"))
        self.exam.setText(s.get("exam_max", "60"))
        for section in SECTIONS:
            self.load_grades(section)

    def load_grades(self, section, default=False):
        t = self.grade_tables[section]
        if default:
            rows = [{"min_score": a, "max_score": b, "grade": c, "remark": d}
                    for a, b, c, d in DEFAULT_GRADES[section]]
        else:
            rows = self.db.grade_scale(section)
        t.setRowCount(0)
        for g in rows:
            r = t.rowCount()
            t.insertRow(r)
            for c, v in enumerate([fmt(g["min_score"], 2), fmt(g["max_score"], 2),
                                   g["grade"], g["remark"]]):
                t.setItem(r, c, cell(v, editable=True))

    def add_grade_row(self, t):
        r = t.rowCount()
        t.insertRow(r)
        for c in range(4):
            t.setItem(r, c, cell("", editable=True))

    def set_logo(self, path):
        self.logo_path = path
        if path and os.path.exists(path):
            self.logo_preview.setPixmap(QPixmap(path).scaled(
                100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            self.logo_preview.clear()
            self.logo_preview.setText("No logo")

    def choose_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose school logo",
                                              os.path.expanduser("~"),
                                              "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            ext = os.path.splitext(path)[1].lower()
            dest = os.path.join(data_dir(), "school_logo" + ext)
            if os.path.abspath(path) != os.path.abspath(dest):
                shutil.copyfile(path, dest)
            self.set_logo(dest)

    def save(self):
        # Check numbers
        try:
            ca1, ca2, exam = float(self.ca1.text()), float(self.ca2.text()), float(self.exam.text())
        except ValueError:
            return warn(self, "Maximum scores must be numbers.")
        if abs(ca1 + ca2 + exam - 100) > 0.001:
            return warn(self, f"C.A. 1 + C.A. 2 + Exam must add up to 100 "
                              f"(now {fmt(ca1 + ca2 + exam)}).")
        days = self.days_opened.text().strip() or "0"
        if not days.isdigit():
            return warn(self, "Times school opened must be a whole number.")
        if not self.session.text().strip():
            return warn(self, "Enter the current session, e.g. 2026/2027.")

        grade_data = {}
        for section, t in self.grade_tables.items():
            rows = []
            for r in range(t.rowCount()):
                vals = [(t.item(r, c).text().strip() if t.item(r, c) else "") for c in range(4)]
                if not any(vals):
                    continue
                try:
                    lo, hi = float(vals[0]), float(vals[1])
                except ValueError:
                    return warn(self, f"{section} grading, row {r + 1}: 'From' and 'To' "
                                      "must be numbers.")
                if lo > hi or not vals[2]:
                    return warn(self, f"{section} grading, row {r + 1} is not correct.")
                rows.append({"min_score": lo, "max_score": hi, "grade": vals[2],
                             "remark": vals[3]})
            if not rows:
                return warn(self, f"The {section} grading scale is empty.")
            grade_data[section] = rows

        for key, w in self.fields.items():
            self.db.set_setting(key, w.text().strip())
        self.db.set_setting("logo_path", self.logo_path)
        self.db.set_setting("current_session", self.session.text().strip())
        self.db.set_setting("current_term", self.term.currentText())
        self.db.set_setting("next_term_begins", self.next_term.text().strip())
        self.db.set_setting("days_school_opened", days)
        self.db.set_setting("ca1_max", fmt(ca1, 2))
        self.db.set_setting("ca2_max", fmt(ca2, 2))
        self.db.set_setting("exam_max", fmt(exam, 2))
        for section, rows in grade_data.items():
            self.db.replace_grade_scale(section, rows)
        info(self, "Settings saved.")
        win = self.window()
        if hasattr(win, "update_top_bar"):
            win.update_top_bar()
