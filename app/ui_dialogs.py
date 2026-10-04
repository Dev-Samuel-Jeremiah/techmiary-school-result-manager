"""
ui_dialogs.py - Pop-up windows: login, change password, student form,
user form, class form and subject pickers.
"""

import os
import shutil
import time

from qtpy.QtCore import Qt, QDate
from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import (QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
                               QFileDialog, QFormLayout, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QPushButton,
                               QTextEdit, QVBoxLayout)

from branding import COMPANY_NAME, COMPANY_URL, COMPANY_WEBSITE, PRODUCT_NAME
from database import SECTIONS, data_dir
from ui_common import fill_combo, secondary, set_combo_data, warn, PRIMARY


# ----------------------------------------------------------------------
# Login
# ----------------------------------------------------------------------
class LoginDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = None
        self.setWindowTitle(f"{PRODUCT_NAME} - Login")
        self.setMinimumWidth(380)

        school = QLabel(db.get_setting("school_name"))
        school.setAlignment(Qt.AlignmentFlag.AlignCenter)
        school.setWordWrap(True)
        school.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {PRIMARY};")
        sub = QLabel(PRODUCT_NAME)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #555;")

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo = db.get_setting("logo_path")
        has_logo = bool(logo and os.path.exists(logo))
        if has_logo:
            logo_label.setPixmap(QPixmap(logo).scaled(
                90, 90, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.returnPressed.connect(self.try_login)
        self.username.returnPressed.connect(self.password.setFocus)

        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.try_login)
        login_btn.setDefault(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(10)
        if has_logo:
            layout.addWidget(logo_label)
        layout.addWidget(school)
        layout.addWidget(sub)
        layout.addSpacing(10)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(login_btn)

        if db.authenticate("admin", "admin123"):
            hint = QLabel("First time? Log in with username <b>admin</b> and password "
                          "<b>admin123</b>. You will be asked to change it.")
            hint.setWordWrap(True)
            hint.setStyleSheet("color: #666; font-size: 9pt;")
            layout.addWidget(hint)

        layout.addSpacing(6)
        footer = QLabel(f'\u00a9 {COMPANY_NAME}<br>'
                        f'<a href="{COMPANY_URL}">{COMPANY_WEBSITE}</a>')
        footer.setOpenExternalLinks(True)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #777; font-size: 8pt;")
        layout.addWidget(footer)

    def try_login(self):
        user = self.db.authenticate(self.username.text(), self.password.text())
        if not user:
            warn(self, "Wrong username or password, or the account is disabled.")
            self.password.clear()
            self.password.setFocus()
            return
        self.user = user
        self.accept()


class ChangePasswordDialog(QDialog):
    def __init__(self, db, user, forced=False, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.setWindowTitle("Change Password")
        self.setMinimumWidth(360)

        self.old = QLineEdit()
        self.new = QLineEdit()
        self.again = QLineEdit()
        for w in (self.old, self.new, self.again):
            w.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow("Current password:", self.old)
        form.addRow("New password:", self.new)
        form.addRow("Repeat new password:", self.again)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        if forced:
            note = QLabel("For security, please set a new password before continuing.")
            note.setWordWrap(True)
            layout.addWidget(note)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def save(self):
        if not self.db.authenticate(self.user["username"], self.old.text()):
            warn(self, "Current password is not correct.")
            return
        if len(self.new.text()) < 6:
            warn(self, "New password must be at least 6 characters.")
            return
        if self.new.text() != self.again.text():
            warn(self, "The new passwords do not match.")
            return
        if self.new.text() == self.old.text():
            warn(self, "Choose a password different from the current one.")
            return
        self.db.set_password(self.user["id"], self.new.text(), must_change=False)
        self.accept()


# ----------------------------------------------------------------------
# Student form
# ----------------------------------------------------------------------
NIGERIAN_STATES = ["", "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue",
                   "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "FCT",
                   "Gombe", "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi",
                   "Kwara", "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo",
                   "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara", "Other"]


class StudentDialog(QDialog):
    def __init__(self, db, student=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.student = student
        self.photo_path = (student or {}).get("photo_path", "") or ""
        self.setWindowTitle("Edit Student" if student else "Register New Student")
        self.setMinimumWidth(640)

        self.admission_no = QLineEdit()
        self.surname = QLineEdit()
        self.first_name = QLineEdit()
        self.other_name = QLineEdit()
        self.gender = QComboBox()
        self.gender.addItems(["", "Male", "Female"])
        self.dob = QDateEdit()
        self.dob.setCalendarPopup(True)
        self.dob.setDisplayFormat("dd/MM/yyyy")
        self.dob.setSpecialValueText(" ")
        self.dob.setMinimumDate(QDate(1950, 1, 1))
        self.dob.setDate(self.dob.minimumDate())
        self.class_combo = QComboBox()
        fill_combo(self.class_combo, [(c["name"], c["id"]) for c in db.list_classes()],
                   empty_label="-- Select class --")
        self.religion = QComboBox()
        self.religion.addItems(["", "Christianity", "Islam", "Other"])
        self.state = QComboBox()
        self.state.addItems(NIGERIAN_STATES)
        self.lga = QLineEdit()
        self.guardian_name = QLineEdit()
        self.guardian_phone = QLineEdit()
        self.address = QTextEdit()
        self.address.setFixedHeight(60)
        self.date_admitted = QDateEdit(QDate.currentDate())
        self.date_admitted.setCalendarPopup(True)
        self.date_admitted.setDisplayFormat("dd/MM/yyyy")
        self.status = QComboBox()
        self.status.addItems(["Active", "Graduated", "Left", "Suspended"])

        # Photo
        self.photo_label = QLabel("No photo")
        self.photo_label.setFixedSize(130, 150)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setStyleSheet("border: 1px dashed #999; background: white;")
        photo_btn = secondary(QPushButton("Choose Photo"))
        photo_btn.clicked.connect(self.choose_photo)
        clear_photo = secondary(QPushButton("Remove Photo"))
        clear_photo.clicked.connect(self.remove_photo)

        form = QGridLayout()
        rows = [
            ("Admission No.*", self.admission_no, "Class*", self.class_combo),
            ("Surname*", self.surname, "First Name*", self.first_name),
            ("Other Name", self.other_name, "Gender*", self.gender),
            ("Date of Birth", self.dob, "Religion", self.religion),
            ("State of Origin", self.state, "L.G.A.", self.lga),
            ("Parent/Guardian", self.guardian_name, "Guardian Phone", self.guardian_phone),
            ("Date Admitted", self.date_admitted, "Status", self.status),
        ]
        for r, (l1, w1, l2, w2) in enumerate(rows):
            form.addWidget(QLabel(l1), r, 0)
            form.addWidget(w1, r, 1)
            form.addWidget(QLabel(l2), r, 2)
            form.addWidget(w2, r, 3)
        form.addWidget(QLabel("Home Address"), len(rows), 0)
        form.addWidget(self.address, len(rows), 1, 1, 3)

        photo_box = QVBoxLayout()
        photo_box.addWidget(self.photo_label)
        photo_box.addWidget(photo_btn)
        photo_box.addWidget(clear_photo)
        photo_box.addStretch()

        top = QHBoxLayout()
        top.addLayout(form, 1)
        top.addSpacing(10)
        top.addLayout(photo_box)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(QLabel("* required"))
        layout.addWidget(buttons)

        if student:
            self.load(student)
        else:
            self.admission_no.setText(db.next_admission_no())
            self.status.setEnabled(False)
        self.show_photo()

    def load(self, s):
        self.admission_no.setText(s["admission_no"])
        self.surname.setText(s["surname"])
        self.first_name.setText(s["first_name"])
        self.other_name.setText(s.get("other_name") or "")
        self.gender.setCurrentText(s.get("gender") or "")
        if s.get("date_of_birth"):
            d = QDate.fromString(s["date_of_birth"], "yyyy-MM-dd")
            if d.isValid():
                self.dob.setDate(d)
        set_combo_data(self.class_combo, s.get("class_id"))
        self.religion.setCurrentText(s.get("religion") or "")
        self.state.setCurrentText(s.get("state_of_origin") or "")
        self.lga.setText(s.get("lga") or "")
        self.guardian_name.setText(s.get("guardian_name") or "")
        self.guardian_phone.setText(s.get("guardian_phone") or "")
        self.address.setPlainText(s.get("address") or "")
        if s.get("date_admitted"):
            d = QDate.fromString(s["date_admitted"], "yyyy-MM-dd")
            if d.isValid():
                self.date_admitted.setDate(d)
        self.status.setCurrentText(s.get("status") or "Active")

    def show_photo(self):
        if self.photo_path and os.path.exists(self.photo_path):
            self.photo_label.setPixmap(QPixmap(self.photo_path).scaled(
                130, 150, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            self.photo_label.clear()
            self.photo_label.setText("No photo")

    def choose_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose passport photo",
                                              os.path.expanduser("~"),
                                              "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.photo_path = path
            self.show_photo()

    def remove_photo(self):
        self.photo_path = ""
        self.show_photo()

    def save(self):
        if not self.admission_no.text().strip():
            return warn(self, "Admission number is required.")
        if not self.surname.text().strip() or not self.first_name.text().strip():
            return warn(self, "Surname and first name are required.")
        if not self.class_combo.currentData():
            return warn(self, "Please select a class. (Create classes first under "
                              "'Classes & Subjects'.)")
        if not self.gender.currentText():
            return warn(self, "Please select gender.")
        existing = self.db.query_one("SELECT id FROM students WHERE admission_no=?",
                                     (self.admission_no.text().strip(),))
        if existing and (not self.student or existing["id"] != self.student["id"]):
            return warn(self, "Another student already has this admission number.")

        # Copy the photo into the app's own folder so it is never lost
        photo = self.photo_path
        photos_dir = os.path.join(data_dir(), "photos")
        if photo and os.path.exists(photo) and \
                os.path.dirname(os.path.abspath(photo)) != os.path.abspath(photos_dir):
            ext = os.path.splitext(photo)[1].lower() or ".jpg"
            safe_no = "".join(ch if ch.isalnum() else "_" for ch in self.admission_no.text())
            dest = os.path.join(photos_dir, f"{safe_no}_{int(time.time())}{ext}")
            shutil.copyfile(photo, dest)
            photo = dest

        dob = "" if self.dob.date() == self.dob.minimumDate() else \
            self.dob.date().toString("yyyy-MM-dd")
        data = {
            "admission_no": self.admission_no.text().strip(),
            "surname": self.surname.text().strip(),
            "first_name": self.first_name.text().strip(),
            "other_name": self.other_name.text().strip(),
            "gender": self.gender.currentText(),
            "date_of_birth": dob,
            "class_id": self.class_combo.currentData(),
            "guardian_name": self.guardian_name.text().strip(),
            "guardian_phone": self.guardian_phone.text().strip(),
            "address": self.address.toPlainText().strip(),
            "state_of_origin": self.state.currentText(),
            "lga": self.lga.text().strip(),
            "religion": self.religion.currentText(),
            "photo_path": photo or "",
            "date_admitted": self.date_admitted.date().toString("yyyy-MM-dd"),
            "status": self.status.currentText(),
        }
        self.db.save_student(data, self.student["id"] if self.student else None)
        self.accept()


# ----------------------------------------------------------------------
# User (staff) form
# ----------------------------------------------------------------------
class UserDialog(QDialog):
    def __init__(self, db, user=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.setWindowTitle("Edit Staff Account" if user else "New Staff Account")
        self.setMinimumWidth(380)

        self.username = QLineEdit()
        self.full_name = QLineEdit()
        self.phone = QLineEdit()
        self.role = QComboBox()
        self.role.addItem("Teacher", "teacher")
        self.role.addItem("Administrator", "admin")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.active = QCheckBox("Account is active (can log in)")
        self.active.setChecked(True)

        form = QFormLayout()
        form.addRow("Full name*:", self.full_name)
        form.addRow("Username*:", self.username)
        form.addRow("Phone:", self.phone)
        form.addRow("Role:", self.role)
        if not user:
            form.addRow("Password*:", self.password)
        form.addRow("", self.active)

        if user:
            self.username.setText(user["username"])
            self.username.setEnabled(False)
            self.full_name.setText(user["full_name"])
            self.phone.setText(user.get("phone") or "")
            set_combo_data(self.role, user["role"])
            self.active.setChecked(bool(user["active"]))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        if not user:
            note = QLabel("The staff member will be asked to change this password "
                          "the first time they log in.")
            note.setWordWrap(True)
            note.setStyleSheet("color: #666;")
            layout.addWidget(note)
        layout.addWidget(buttons)

    def save(self):
        name = self.full_name.text().strip()
        if not name:
            return warn(self, "Full name is required.")
        if self.user:
            becoming_non_admin = self.user["role"] == "admin" and (
                self.role.currentData() != "admin" or not self.active.isChecked())
            if becoming_non_admin and self.db.count_admins() <= 1:
                return warn(self, "This is the only active administrator. "
                                  "Create another administrator first.")
            self.db.update_user(self.user["id"], name, self.role.currentData(),
                                self.phone.text().strip(), self.active.isChecked())
        else:
            username = self.username.text().strip()
            if not username or " " in username:
                return warn(self, "Enter a username without spaces.")
            if len(self.password.text()) < 6:
                return warn(self, "Password must be at least 6 characters.")
            if self.db.query_one("SELECT id FROM users WHERE username=?", (username,)):
                return warn(self, "That username is already taken.")
            uid = self.db.add_user(username, name, self.role.currentData(),
                                   self.password.text(), self.phone.text().strip())
            if not self.active.isChecked():
                self.db.update_user(uid, name, self.role.currentData(),
                                    self.phone.text().strip(), False)
        self.accept()


# ----------------------------------------------------------------------
# Class form
# ----------------------------------------------------------------------
class ClassDialog(QDialog):
    def __init__(self, db, klass=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.klass = klass
        self.setWindowTitle("Edit Class" if klass else "New Class")
        self.setMinimumWidth(360)

        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g. JSS 1A, Primary 4, SS 2 Science")
        self.section = QComboBox()
        for s in SECTIONS:
            self.section.addItem(s, s)
        self.teacher = QComboBox()
        fill_combo(self.teacher, [(u["full_name"], u["id"])
                                  for u in db.list_users(active_only=True)],
                   empty_label="-- None --")
        self.add_subjects = QCheckBox("Add all subjects of this section to the class")
        self.add_subjects.setChecked(True)

        form = QFormLayout()
        form.addRow("Class name*:", self.name)
        form.addRow("Section:", self.section)
        form.addRow("Class (form) teacher:", self.teacher)
        if not klass:
            form.addRow("", self.add_subjects)

        if klass:
            self.name.setText(klass["name"])
            set_combo_data(self.section, klass["section"])
            set_combo_data(self.teacher, klass.get("form_teacher_id"))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def save(self):
        name = self.name.text().strip()
        if not name:
            return warn(self, "Class name is required.")
        other = self.db.query_one("SELECT id FROM classes WHERE name=?", (name,))
        if other and (not self.klass or other["id"] != self.klass["id"]):
            return warn(self, "A class with this name already exists.")
        section = self.section.currentData()
        teacher = self.teacher.currentData()
        if self.klass:
            self.db.update_class(self.klass["id"], name, section, teacher)
        else:
            cid = self.db.add_class(name, section, teacher)
            if self.add_subjects.isChecked():
                for s in self.db.list_subjects(section):
                    self.db.add_class_subject(cid, s["id"])
        self.accept()


# ----------------------------------------------------------------------
# Pick subjects for a class
# ----------------------------------------------------------------------
class PickSubjectsDialog(QDialog):
    def __init__(self, db, klass, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Add subjects to {klass['name']}")
        self.setMinimumSize(380, 460)
        taken = {c["subject_id"] for c in db.class_subjects(klass["id"])}
        self.list = QListWidget()
        for s in db.list_subjects(klass["section"]):
            if s["id"] in taken:
                continue
            item = QListWidgetItem(s["name"])
            item.setData(Qt.ItemDataRole.UserRole, s["id"])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list.addItem(item)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Tick the {klass['section'].lower()} subjects to add:"))
        layout.addWidget(self.list)
        if self.list.count() == 0:
            layout.addWidget(QLabel("All subjects are already added. Use 'Subject List' "
                                    "to create new subjects."))
        layout.addWidget(buttons)

    def chosen(self):
        return [self.list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.list.count())
                if self.list.item(i).checkState() == Qt.CheckState.Checked]


class PickTeacherDialog(QDialog):
    def __init__(self, db, current=None, title="Choose teacher", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(320)
        self.combo = QComboBox()
        fill_combo(self.combo, [(u["full_name"], u["id"])
                                for u in db.list_users(active_only=True)],
                   empty_label="-- No teacher --")
        set_combo_data(self.combo, current)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Teacher:"))
        layout.addWidget(self.combo)
        layout.addWidget(buttons)

    def teacher_id(self):
        return self.combo.currentData()


class SubjectListDialog(QDialog):
    """Add or delete subjects in the master list."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Subject List")
        self.setMinimumSize(460, 520)

        self.section = QComboBox()
        for s in SECTIONS:
            self.section.addItem(s, s)
        self.section.currentIndexChanged.connect(self.refresh)
        self.list = QListWidget()
        self.new_name = QLineEdit()
        self.new_name.setPlaceholderText("New subject name")
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add)
        self.new_name.returnPressed.connect(self.add)
        del_btn = QPushButton("Delete Selected")
        del_btn.setProperty("danger", True)
        del_btn.clicked.connect(self.delete)
        close_btn = secondary(QPushButton("Close"))
        close_btn.clicked.connect(self.accept)

        top = QHBoxLayout()
        top.addWidget(QLabel("Section:"))
        top.addWidget(self.section, 1)
        add_row = QHBoxLayout()
        add_row.addWidget(self.new_name, 1)
        add_row.addWidget(add_btn)
        bottom = QHBoxLayout()
        bottom.addWidget(del_btn)
        bottom.addStretch()
        bottom.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.list)
        layout.addLayout(add_row)
        layout.addLayout(bottom)
        self.refresh()

    def refresh(self):
        self.list.clear()
        for s in self.db.list_subjects(self.section.currentData()):
            item = QListWidgetItem(s["name"])
            item.setData(Qt.ItemDataRole.UserRole, s["id"])
            self.list.addItem(item)

    def add(self):
        name = self.new_name.text().strip()
        if not name:
            return
        if self.db.query_one("SELECT id FROM subjects WHERE name=? AND section=?",
                             (name, self.section.currentData())):
            return warn(self, "That subject already exists.")
        self.db.add_subject(name, self.section.currentData())
        self.new_name.clear()
        self.refresh()

    def delete(self):
        item = self.list.currentItem()
        if not item:
            return
        from ui_common import confirm
        if confirm(self, f"Delete '{item.text()}'? All scores recorded for this subject "
                         "will also be deleted."):
            self.db.delete_subject(item.data(Qt.ItemDataRole.UserRole))
            self.refresh()
