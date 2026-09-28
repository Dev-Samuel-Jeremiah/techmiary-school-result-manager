"""
pages_results.py - Screens for teachers and results:
Enter Scores, Remarks & Attendance, and Results (print / PDF).
"""

from PySide6.QtCore import QEvent, QRegularExpression, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QKeySequence, QRegularExpressionValidator,
                           QShortcut)
from PySide6.QtWidgets import (QAbstractItemDelegate, QAbstractItemView, QApplication,
                               QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QStyledItemDelegate)

from pages_admin import Page
from results import (SHEET_CSS, broadsheet_html, build_results_html, compute_class_results,
                     fmt, grade_for, ordinal, suggest_comment)
from ui_common import (ResultDocument, cell, confirm, error, fill_combo, info, make_table,
                       print_preview, save_pdf, secondary, selected_rows_data,
                       session_combo, term_combo, warn)

RED = QBrush(QColor("#ffd6d6"))
NONE = QBrush()


class NumberDelegate(QStyledItemDelegate):
    """Editor that only accepts numbers, and moves down a row when Enter is pressed
    (so a teacher can type a whole column quickly)."""

    def __init__(self, table):
        super().__init__(table)
        self.table = table

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QRegularExpressionValidator(
            QRegularExpression(r"^\d{0,3}(\.\d{0,2})?$"), editor))
        editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return editor

    def eventFilter(self, editor, event):
        if event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return,
                                                                    Qt.Key.Key_Enter):
            self.commitData.emit(editor)
            self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.NoHint)
            QTimer.singleShot(0, self.move_down)
            return True
        return super().eventFilter(editor, event)

    def move_down(self):
        t = self.table
        r, c = t.currentRow(), t.currentColumn()
        if r + 1 < t.rowCount():
            t.setCurrentCell(r + 1, c)
            t.editItem(t.item(r + 1, c))


# ======================================================================
# Enter scores
# ======================================================================
class ScoresPage(Page):
    title = "Enter Scores"
    COL_CA1, COL_CA2, COL_EXAM, COL_TOTAL, COL_GRADE = 3, 4, 5, 6, 7

    def __init__(self, db, user):
        super().__init__(db, user)
        self.dirty = False
        self.loaded = None  # (class_id, subject_id, session, term)
        self.maxes = db.max_scores()
        self.scale = []

        self.session = session_combo(db)
        self.term = term_combo(db)
        if not self.is_admin:
            # Teachers can only enter scores for the current session and term
            self.session.setEnabled(False)
            self.term.setEnabled(False)
        self.assignment = QComboBox()
        self.assignment.setMinimumWidth(320)
        load = QPushButton("Load Students")
        load.clicked.connect(self.load)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Class & Subject:"))
        bar.addWidget(self.assignment, 2)
        bar.addWidget(QLabel("Session:"))
        bar.addWidget(self.session)
        bar.addWidget(QLabel("Term:"))
        bar.addWidget(self.term)
        bar.addWidget(load)
        self.layout_.addLayout(bar)

        self.hint = QLabel()
        self.hint.setStyleSheet("color: #555;")
        self.layout_.addWidget(self.hint)

        self.table = make_table(["S/N", "Adm. No", "Student Name", "CA 1", "CA 2", "Exam",
                                 "Total", "Grade"], stretch_column=2, editable=True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.delegate = NumberDelegate(self.table)
        for c in (self.COL_CA1, self.COL_CA2, self.COL_EXAM):
            self.table.setItemDelegateForColumn(c, self.delegate)
        self.table.itemChanged.connect(self.on_changed)
        self.layout_.addWidget(self.table)
        for keys, slot in ((QKeySequence.StandardKey.Paste, self.paste),
                           (QKeySequence.StandardKey.Delete, self.clear_selected)):
            sc = QShortcut(QKeySequence(keys), self.table)
            sc.setContext(Qt.ShortcutContext.WidgetShortcut)
            sc.activated.connect(slot)

        self.status = QLabel()
        paste = secondary(QPushButton("Paste Column from Excel"))
        paste.setToolTip("Copy a column of scores in Excel, click the first cell here, "
                         "then press this button (or Ctrl+V).")
        paste.clicked.connect(self.paste)
        clear = secondary(QPushButton("Clear Selected Cells"))
        clear.clicked.connect(self.clear_selected)
        self.save_btn = QPushButton("Save Scores")
        self.save_btn.clicked.connect(self.save)
        row = QHBoxLayout()
        row.addWidget(self.status)
        row.addStretch()
        row.addWidget(paste)
        row.addWidget(clear)
        row.addWidget(self.save_btn)
        self.layout_.addLayout(row)

    # ----------------------------------------------------------------
    def refresh(self):
        items = [(f"{a['class_name']}  —  {a['subject']}", (a["class_id"], a["subject_id"]))
                 for a in self.db.teacher_assignments(self.user)]
        fill_combo(self.assignment, items)
        if not self.is_admin:
            self.session.setCurrentText(self.db.get_setting("current_session"))
            idx = self.term.findData(self.db.get_setting("current_term"))
            self.term.setCurrentIndex(max(idx, 0))
        self.maxes = self.db.max_scores()
        a, b, c = self.maxes
        self.table.horizontalHeaderItem(self.COL_CA1).setText(f"CA 1 ({fmt(a)})")
        self.table.horizontalHeaderItem(self.COL_CA2).setText(f"CA 2 ({fmt(b)})")
        self.table.horizontalHeaderItem(self.COL_EXAM).setText(f"Exam ({fmt(c)})")
        if not items:
            self.hint.setText("No subjects have been assigned to you yet. Ask the "
                              "administrator to assign you under 'Classes & Subjects'.")
        else:
            self.hint.setText("Pick a class and subject, then click 'Load Students'. Type a "
                              "score and press Enter to move down. Leave a cell empty if the "
                              "student has no score.")

    def can_leave(self):
        if self.dirty:
            return confirm(self, "You have unsaved scores. Leave without saving?")
        return True

    def load(self):
        if self.dirty and not confirm(self, "You have unsaved scores. Discard them?"):
            return
        pair = self.assignment.currentData()
        if not pair:
            return info(self, "Choose a class and subject first.")
        session = self.session.currentText().strip()
        if not session:
            return warn(self, "Enter a session, e.g. 2026/2027.")
        class_id, subject_id = pair
        term = self.term.currentData()
        klass = self.db.get_class(class_id)
        self.scale = self.db.grade_scale(klass["section"])
        rows = self.db.get_scores(class_id, subject_id, session, term)

        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for i, r in enumerate(rows, start=1):
            n = self.table.rowCount()
            self.table.insertRow(n)
            self.table.setItem(n, 0, cell(i, r["student_id"], align="center"))
            self.table.setItem(n, 1, cell(r["admission_no"]))
            self.table.setItem(n, 2, cell(r["name"]))
            for col, key in ((self.COL_CA1, "ca1"), (self.COL_CA2, "ca2"),
                             (self.COL_EXAM, "exam")):
                self.table.setItem(n, col, cell(fmt(r[key]) if r[key] is not None else "",
                                                editable=True, align="center"))
            self.table.setItem(n, self.COL_TOTAL, cell("", align="center"))
            self.table.setItem(n, self.COL_GRADE, cell("", align="center"))
            self.update_row(n)
        self.table.blockSignals(False)

        self.loaded = (class_id, subject_id, session, term)
        self.dirty = False
        self.status.setText(f"{len(rows)} student(s) in {klass['name']}.")
        if not rows:
            info(self, "There are no active students in this class yet.")

    # ----------------------------------------------------------------
    def parse(self, row, col):
        item = self.table.item(row, col)
        text = item.text().strip() if item else ""
        if text == "":
            return None, True
        try:
            v = float(text)
        except ValueError:
            return None, False
        limit = self.maxes[col - self.COL_CA1]
        return v, 0 <= v <= limit

    def update_row(self, row):
        values = []
        all_ok = True
        for col in (self.COL_CA1, self.COL_CA2, self.COL_EXAM):
            v, ok = self.parse(row, col)
            self.table.item(row, col).setBackground(NONE if ok else RED)
            all_ok = all_ok and ok
            values.append(v if ok else None)
        if any(v is not None for v in values) and all_ok:
            total = sum(v or 0 for v in values)
            self.table.item(row, self.COL_TOTAL).setText(fmt(total))
            self.table.item(row, self.COL_GRADE).setText(grade_for(total, self.scale)[0])
        else:
            self.table.item(row, self.COL_TOTAL).setText("")
            self.table.item(row, self.COL_GRADE).setText("" if all_ok else "!")
        return all_ok

    def on_changed(self, item):
        if item.column() in (self.COL_CA1, self.COL_CA2, self.COL_EXAM):
            self.table.blockSignals(True)
            self.update_row(item.row())
            self.table.blockSignals(False)
            self.dirty = True
            self.status.setText("Unsaved changes...")

    def paste(self):
        """Paste scores copied from Excel / a spreadsheet, starting at the current cell."""
        text = QApplication.clipboard().text()
        if not text or self.table.rowCount() == 0:
            return
        start_r = max(self.table.currentRow(), 0)
        start_c = self.table.currentColumn()
        if start_c not in (self.COL_CA1, self.COL_CA2, self.COL_EXAM):
            return info(self, "Click the first CA 1, CA 2 or Exam cell to paste into.")
        lines = [ln for ln in text.replace("\r", "").split("\n") if ln != ""]
        for i, line in enumerate(lines):
            r = start_r + i
            if r >= self.table.rowCount():
                break
            for j, value in enumerate(line.split("\t")):
                c = start_c + j
                if c > self.COL_EXAM:
                    break
                self.table.item(r, c).setText(value.strip())

    def clear_selected(self):
        for item in self.table.selectedItems():
            if item.column() in (self.COL_CA1, self.COL_CA2, self.COL_EXAM):
                item.setText("")

    def save(self):
        if not self.loaded:
            return info(self, "Load students first.")
        bad = [r + 1 for r in range(self.table.rowCount()) if not self.update_row(r)]
        if bad:
            a, b, c = self.maxes
            return warn(self, "Some scores are not correct (shown in red) on row(s): "
                              f"{', '.join(map(str, bad[:15]))}.\n\nMaximums: CA 1 = {fmt(a)}, "
                              f"CA 2 = {fmt(b)}, Exam = {fmt(c)}.")
        class_id, subject_id, session, term = self.loaded
        try:
            for r in range(self.table.rowCount()):
                sid = self.table.item(r, 0).data(Qt.ItemDataRole.UserRole)
                ca1 = self.parse(r, self.COL_CA1)[0]
                ca2 = self.parse(r, self.COL_CA2)[0]
                exam = self.parse(r, self.COL_EXAM)[0]
                self.db.save_score(sid, class_id, subject_id, session, term,
                                   ca1, ca2, exam, self.user["id"])
            self.db.commit()
        except Exception as exc:  # keep the app running if something goes wrong
            self.db.conn.rollback()
            return error(self, f"Could not save scores:\n{exc}")
        self.dirty = False
        self.status.setText("All scores saved.")
        info(self, "Scores saved successfully.")


# ======================================================================
# Remarks & attendance
# ======================================================================
class RemarksPage(Page):
    title = "Remarks & Attendance"
    COL_DAYS, COL_TEACHER, COL_PRINCIPAL = 5, 6, 7

    def __init__(self, db, user):
        super().__init__(db, user)
        self.loaded = None
        self.class_combo = QComboBox()
        self.class_combo.setMinimumWidth(180)
        self.session = session_combo(db)
        self.term = term_combo(db)
        load = QPushButton("Load")
        load.clicked.connect(self.load)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Class:"))
        bar.addWidget(self.class_combo, 1)
        bar.addWidget(QLabel("Session:"))
        bar.addWidget(self.session)
        bar.addWidget(QLabel("Term:"))
        bar.addWidget(self.term)
        bar.addWidget(load)
        self.layout_.addLayout(bar)

        head_label = "Principal / Head Teacher's Comment"
        self.table = make_table(["Adm. No", "Student Name", "Average", "Position", "Grade",
                                 "Days Present", "Class Teacher's Comment", head_label],
                                editable=True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setColumnWidth(self.COL_TEACHER, 280)
        self.table.setColumnWidth(self.COL_PRINCIPAL, 280)
        self.table.setWordWrap(True)
        self.layout_.addWidget(self.table)

        auto_t = secondary(QPushButton("Auto-fill Empty Teacher Comments"))
        auto_t.clicked.connect(lambda: self.autofill(self.COL_TEACHER, "teacher"))
        auto_p = secondary(QPushButton("Auto-fill Empty Principal Comments"))
        auto_p.clicked.connect(lambda: self.autofill(self.COL_PRINCIPAL, "principal"))
        auto_p.setVisible(self.is_admin)
        save = QPushButton("Save")
        save.clicked.connect(self.save)
        self.status = QLabel()
        row = QHBoxLayout()
        row.addWidget(self.status)
        row.addStretch()
        row.addWidget(auto_t)
        row.addWidget(auto_p)
        row.addWidget(save)
        self.layout_.addLayout(row)

    def refresh(self):
        fill_combo(self.class_combo, [(c["name"], c["id"])
                                      for c in self.db.form_classes(self.user)])
        opened = self.db.get_setting("days_school_opened", "0")
        self.status.setText(f"Times school opened this term: {opened} (change in Settings).")

    def load(self):
        class_id = self.class_combo.currentData()
        if not class_id:
            return info(self, "You are not a class teacher of any class.")
        session = self.session.currentText().strip()
        term = self.term.currentData()
        data = compute_class_results(self.db, class_id, session, term)
        perf = {s["id"]: s for s in data["students"]}
        rows = self.db.get_term_reports(class_id, session, term)

        self.table.setRowCount(0)
        for r in rows:
            p = perf.get(r["student_id"], {})
            n = self.table.rowCount()
            self.table.insertRow(n)
            self.table.setItem(n, 0, cell(r["admission_no"], r["student_id"]))
            self.table.setItem(n, 1, cell(r["name"]))
            self.table.setItem(n, 2, cell(fmt(p.get("average"), 2), p.get("average"),
                                          align="center"))
            self.table.setItem(n, 3, cell(ordinal(p.get("position")) if p.get("position")
                                          else "-", align="center"))
            self.table.setItem(n, 4, cell(p.get("grade", "-"), align="center"))
            self.table.setItem(n, self.COL_DAYS, cell(
                "" if r["days_present"] is None else r["days_present"], editable=True,
                align="center"))
            self.table.setItem(n, self.COL_TEACHER, cell(r["teacher_comment"] or "",
                                                         editable=True))
            self.table.setItem(n, self.COL_PRINCIPAL, cell(r["principal_comment"] or "",
                                                           editable=self.is_admin))
        self.loaded = (class_id, session, term)

    def autofill(self, col, role):
        if not self.loaded:
            return info(self, "Load a class first.")
        filled = 0
        for r in range(self.table.rowCount()):
            item = self.table.item(r, col)
            avg = self.table.item(r, 2).data(Qt.ItemDataRole.UserRole)
            if item and not item.text().strip() and avg is not None:
                item.setText(suggest_comment(avg, role))
                filled += 1
        info(self, f"{filled} comment(s) filled. You can edit any of them. Remember to Save.")

    def save(self):
        if not self.loaded:
            return info(self, "Load a class first.")
        class_id, session, term = self.loaded
        opened = self.db.get_setting("days_school_opened", "0")
        opened = int(opened) if opened.isdigit() else 0
        for r in range(self.table.rowCount()):
            days = self.table.item(r, self.COL_DAYS).text().strip()
            if days and not days.isdigit():
                return warn(self, f"Row {r + 1}: days present must be a whole number.")
            if days and opened and int(days) > opened:
                return warn(self, f"Row {r + 1}: days present ({days}) is more than the "
                                  f"times school opened ({opened}).")
        for r in range(self.table.rowCount()):
            sid = self.table.item(r, 0).data(Qt.ItemDataRole.UserRole)
            days = self.table.item(r, self.COL_DAYS).text().strip()
            self.db.save_term_report(sid, class_id, session, term,
                                     int(days) if days else None,
                                     self.table.item(r, self.COL_TEACHER).text().strip(),
                                     self.table.item(r, self.COL_PRINCIPAL).text().strip())
        self.db.commit()
        info(self, "Remarks and attendance saved.")


# ======================================================================
# Results
# ======================================================================
class ResultsPage(Page):
    title = "Results & Printing"

    def __init__(self, db, user):
        super().__init__(db, user)
        self.loaded = None
        self.class_combo = QComboBox()
        self.class_combo.setMinimumWidth(180)
        self.session = session_combo(db)
        self.term = term_combo(db)
        load = QPushButton("Show Results")
        load.clicked.connect(self.load)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Class:"))
        bar.addWidget(self.class_combo, 1)
        bar.addWidget(QLabel("Session:"))
        bar.addWidget(self.session)
        bar.addWidget(QLabel("Term:"))
        bar.addWidget(self.term)
        bar.addWidget(load)
        self.layout_.addLayout(bar)

        self.table = make_table(["Position", "Adm. No", "Student Name", "Subjects",
                                 "Total", "Average", "Grade", "Remark"],
                                stretch_column=2, multi_select=True)
        self.table.doubleClicked.connect(lambda *_: self.preview(selected_only=True))
        self.layout_.addWidget(self.table)

        self.summary = QLabel()
        self.layout_.addWidget(self.summary)

        b1 = QPushButton("Print Selected")
        b1.clicked.connect(lambda: self.preview(selected_only=True))
        b2 = QPushButton("Print Whole Class")
        b2.clicked.connect(lambda: self.preview(selected_only=False))
        b3 = secondary(QPushButton("Save Class Results as PDF"))
        b3.clicked.connect(self.export_pdf)
        b4 = secondary(QPushButton("Broadsheet"))
        b4.clicked.connect(self.broadsheet)
        row = QHBoxLayout()
        row.addWidget(QLabel("Tip: double-click a student to preview their result."))
        row.addStretch()
        for b in (b4, b3, b1, b2):
            row.addWidget(b)
        self.layout_.addLayout(row)

    def refresh(self):
        fill_combo(self.class_combo, [(c["name"], c["id"])
                                      for c in self.db.form_classes(self.user)])

    def current(self):
        class_id = self.class_combo.currentData()
        if not class_id:
            info(self, "No class available. (Teachers can only print results for the class "
                       "they are class teacher of.)")
            return None
        return class_id, self.session.currentText().strip(), self.term.currentData()

    def load(self):
        cur = self.current()
        if not cur:
            return
        class_id, session, term = cur
        data = compute_class_results(self.db, class_id, session, term)
        ordered = sorted(data["students"],
                         key=lambda s: (s["position"] is None, s["position"] or 0, s["surname"]))
        self.table.setRowCount(0)
        for s in ordered:
            n = self.table.rowCount()
            self.table.insertRow(n)
            vals = [ordinal(s["position"]) if s["position"] else "-", s["admission_no"],
                    f"{s['surname'].upper()} {s['first_name']} {s.get('other_name') or ''}",
                    s["subjects_taken"], fmt(s["total"]), fmt(s["average"], 2), s["grade"],
                    s["grade_remark"]]
            for c, v in enumerate(vals):
                self.table.setItem(n, c, cell(v, s["id"] if c == 0 else None,
                                              align=None if c == 2 else "center"))
        offered = len(self.db.class_subjects(class_id))
        missing = [s for s in data["students"] if s["subjects_taken"] < offered]
        text = (f"{data['class_size']} student(s). Class average: "
                f"{fmt(data['class_average'], 2)}.")
        if missing:
            text += (f"  ⚠ {len(missing)} student(s) have scores in fewer than the "
                     f"{offered} subjects offered — some teachers may not have entered "
                     "scores yet.")
        self.summary.setText(text)
        self.loaded = cur

    def make_document(self, student_ids=None):
        class_id, session, term = self.loaded
        html, data = build_results_html(self.db, class_id, session, term, student_ids)
        images = {"logo": self.db.get_setting("logo_path")}
        for s in data["students"]:
            images[f"photo_{s['id']}"] = s.get("photo_path")
        return ResultDocument(html, images, SHEET_CSS), data

    def ensure_loaded(self):
        cur = self.current()
        if not cur:
            return False
        if self.loaded != cur:
            self.load()
        return True

    def preview(self, selected_only):
        if not self.ensure_loaded():
            return
        ids = None
        if selected_only:
            ids = selected_rows_data(self.table)
            if not ids:
                return info(self, "Select one or more students in the list first.")
        if self.table.rowCount() == 0:
            return info(self, "There are no students in this class.")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            doc, _ = self.make_document(ids)
        finally:
            QApplication.restoreOverrideCursor()
        print_preview(self, doc, title="Result Sheets - Print Preview")

    def export_pdf(self):
        if not self.ensure_loaded():
            return
        if self.table.rowCount() == 0:
            return info(self, "There are no students in this class.")
        class_id, session, term = self.loaded
        doc, data = self.make_document()
        name = f"{data['class']['name']} {term} {session} Results".replace("/", "-")
        path = save_pdf(self, doc, name + ".pdf")
        if path:
            info(self, f"Saved:\n{path}")

    def broadsheet(self):
        if not self.ensure_loaded():
            return
        class_id, session, term = self.loaded
        doc = ResultDocument(broadsheet_html(self.db, class_id, session, term), {}, SHEET_CSS)
        print_preview(self, doc, landscape=True, title="Broadsheet - Print Preview")
