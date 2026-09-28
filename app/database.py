"""
database.py - All data storage for Techmiary School Result Manager.

Uses SQLite (built into Python), so there is nothing extra to install.
The database is a single file (school.db) kept in the user's data folder:
  Windows: C:\\Users\\<you>\\AppData\\Roaming\\TechmiarySchoolResultManager\\school.db
  Linux:   ~/.local/share/TechmiarySchoolResultManager/school.db
"""

import hashlib
import os
import secrets
import shutil
import sqlite3
import sys
from datetime import datetime

from branding import DATA_FOLDER, OLD_DATA_FOLDER

APP_NAME = DATA_FOLDER


# ----------------------------------------------------------------------
# Where the data lives
# ----------------------------------------------------------------------
def data_dir():
    """Folder that holds the database, photos and logo."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    path = os.path.join(base, APP_NAME)
    old = os.path.join(base, OLD_DATA_FOLDER)
    # Upgrading from the old "School Result Manager": carry the data across once.
    if not os.path.exists(path) and os.path.isfile(os.path.join(old, "school.db")):
        try:
            shutil.copytree(old, path)
            _repoint_old_paths(os.path.join(path, "school.db"), old, path)
        except (OSError, sqlite3.Error):
            pass
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "photos"), exist_ok=True)
    return path


def _repoint_old_paths(db_file, old, new):
    """Photos and logo paths stored in the copied database still point at the old
    folder; point them at the new one."""
    conn = sqlite3.connect(db_file)
    try:
        conn.execute("UPDATE students SET photo_path = REPLACE(photo_path, ?, ?) "
                     "WHERE photo_path LIKE ?", (old, new, old + "%"))
        conn.execute("UPDATE settings SET value = REPLACE(value, ?, ?) "
                     "WHERE key = 'logo_path' AND value LIKE ?", (old, new, old + "%"))
        conn.commit()
    finally:
        conn.close()


def default_db_path():
    return os.path.join(data_dir(), "school.db")


# ----------------------------------------------------------------------
# Password hashing (never store plain passwords)
# ----------------------------------------------------------------------
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                 salt.encode("utf-8"), 120_000)
    return digest.hex(), salt


def check_password(password, stored_hash, salt):
    digest, _ = hash_password(password, salt)
    return secrets.compare_digest(digest, stored_hash)


# ----------------------------------------------------------------------
# Default values
# ----------------------------------------------------------------------
SECTIONS = ["Primary", "Secondary"]
TERMS = ["First Term", "Second Term", "Third Term"]

DEFAULT_SETTINGS = {
    "school_name": "My School Name",
    "school_address": "School Address, City, State",
    "school_motto": "Knowledge and Character",
    "school_phone": "",
    "school_email": "",
    "logo_path": "",
    "current_session": "2026/2027",
    "current_term": "First Term",
    "next_term_begins": "",
    "days_school_opened": "0",
    "ca1_max": "20",
    "ca2_max": "20",
    "exam_max": "60",
    "principal_name": "",
    "head_teacher_name": "",
}

# (min, max, grade, remark)
DEFAULT_GRADES = {
    "Secondary": [
        (75, 100, "A1", "Excellent"),
        (70, 74.99, "B2", "Very Good"),
        (65, 69.99, "B3", "Good"),
        (60, 64.99, "C4", "Credit"),
        (55, 59.99, "C5", "Credit"),
        (50, 54.99, "C6", "Credit"),
        (45, 49.99, "D7", "Pass"),
        (40, 44.99, "E8", "Pass"),
        (0, 39.99, "F9", "Fail"),
    ],
    "Primary": [
        (70, 100, "A", "Excellent"),
        (60, 69.99, "B", "Very Good"),
        (50, 59.99, "C", "Good"),
        (45, 49.99, "D", "Fair"),
        (40, 44.99, "E", "Pass"),
        (0, 39.99, "F", "Fail"),
    ],
}

DEFAULT_SUBJECTS = {
    "Primary": ["English Language", "Mathematics", "Basic Science and Technology",
                "Social Studies", "Civic Education", "Christian Religious Studies",
                "Islamic Religious Studies", "Cultural and Creative Arts",
                "Physical and Health Education", "Hausa Language",
                "Verbal Reasoning", "Quantitative Reasoning"],
    "Secondary": ["English Language", "Mathematics", "Biology", "Chemistry",
                  "Physics", "Agricultural Science", "Economics", "Government",
                  "Literature in English", "Geography", "Civic Education",
                  "Christian Religious Studies", "Islamic Religious Studies",
                  "Computer Studies", "Basic Science", "Basic Technology",
                  "Business Studies", "Hausa Language"],
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL COLLATE NOCASE,
    full_name     TEXT NOT NULL,
    phone         TEXT DEFAULT '',
    role          TEXT NOT NULL CHECK (role IN ('admin', 'teacher')),
    password_hash TEXT NOT NULL,
    salt          TEXT NOT NULL,
    must_change   INTEGER DEFAULT 0,
    active        INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS classes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT UNIQUE NOT NULL,
    section         TEXT NOT NULL,
    form_teacher_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS subjects (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    section TEXT NOT NULL,
    UNIQUE (name, section)
);

CREATE TABLE IF NOT EXISTS class_subjects (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id   INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE (class_id, subject_id)
);

CREATE TABLE IF NOT EXISTS students (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_no   TEXT UNIQUE NOT NULL,
    surname        TEXT NOT NULL,
    first_name     TEXT NOT NULL,
    other_name     TEXT DEFAULT '',
    gender         TEXT DEFAULT '',
    date_of_birth  TEXT DEFAULT '',
    class_id       INTEGER REFERENCES classes(id) ON DELETE SET NULL,
    guardian_name  TEXT DEFAULT '',
    guardian_phone TEXT DEFAULT '',
    address        TEXT DEFAULT '',
    state_of_origin TEXT DEFAULT '',
    lga            TEXT DEFAULT '',
    religion       TEXT DEFAULT '',
    photo_path     TEXT DEFAULT '',
    date_admitted  TEXT DEFAULT '',
    status         TEXT DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS scores (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id   INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    session    TEXT NOT NULL,
    term       TEXT NOT NULL,
    ca1        REAL,
    ca2        REAL,
    exam       REAL,
    entered_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_at TEXT,
    UNIQUE (student_id, subject_id, session, term)
);

CREATE TABLE IF NOT EXISTS term_reports (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id        INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id          INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    session           TEXT NOT NULL,
    term              TEXT NOT NULL,
    days_present      INTEGER,
    teacher_comment   TEXT DEFAULT '',
    principal_comment TEXT DEFAULT '',
    UNIQUE (student_id, session, term)
);

CREATE TABLE IF NOT EXISTS grade_scales (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    section   TEXT NOT NULL,
    min_score REAL NOT NULL,
    max_score REAL NOT NULL,
    grade     TEXT NOT NULL,
    remark    TEXT NOT NULL
);
"""


class Database:
    """Thin helper around one SQLite connection."""

    def __init__(self, path=None):
        self.path = path or default_db_path()
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self._seed_defaults()

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------
    def query(self, sql, params=()):
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def query_one(self, sql, params=()):
        row = self.conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    def execute(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.lastrowid

    def close(self):
        self.conn.close()

    def backup_to(self, target_path):
        """Make a safe copy of the whole database."""
        dest = sqlite3.connect(target_path)
        with dest:
            self.conn.backup(dest)
        dest.close()

    def restore_from(self, source_path):
        """Replace the current database with a backup file."""
        test = sqlite3.connect(source_path)
        tables = {r[0] for r in test.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        test.close()
        if not {"students", "scores", "users"}.issubset(tables):
            raise ValueError("That file is not a School Result Manager backup.")
        self.conn.close()
        shutil.copyfile(source_path, self.path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)

    # ------------------------------------------------------------------
    # First-run defaults
    # ------------------------------------------------------------------
    def _seed_defaults(self):
        for key, value in DEFAULT_SETTINGS.items():
            self.conn.execute(
                "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (key, value))

        if not self.conn.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            h, s = hash_password("admin123")
            self.conn.execute(
                "INSERT INTO users(username, full_name, role, password_hash, salt, must_change) "
                "VALUES ('admin', 'Administrator', 'admin', ?, ?, 1)", (h, s))

        if not self.conn.execute("SELECT 1 FROM grade_scales LIMIT 1").fetchone():
            for section, rows in DEFAULT_GRADES.items():
                for mn, mx, g, r in rows:
                    self.conn.execute(
                        "INSERT INTO grade_scales(section, min_score, max_score, grade, remark) "
                        "VALUES (?, ?, ?, ?, ?)", (section, mn, mx, g, r))

        if not self.conn.execute("SELECT 1 FROM subjects LIMIT 1").fetchone():
            for section, names in DEFAULT_SUBJECTS.items():
                for n in names:
                    self.conn.execute(
                        "INSERT INTO subjects(name, section) VALUES (?, ?)", (n, section))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    def get_setting(self, key, default=""):
        row = self.query_one("SELECT value FROM settings WHERE key=?", (key,))
        return row["value"] if row and row["value"] is not None else default

    def get_settings(self):
        return {r["key"]: r["value"] for r in self.query("SELECT key, value FROM settings")}

    def set_setting(self, key, value):
        self.execute("INSERT INTO settings(key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))

    def max_scores(self):
        def num(k, d):
            try:
                return float(self.get_setting(k, d))
            except ValueError:
                return float(d)
        return num("ca1_max", 20), num("ca2_max", 20), num("exam_max", 60)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    def authenticate(self, username, password):
        user = self.query_one("SELECT * FROM users WHERE username=?", (username.strip(),))
        if user and user["active"] and check_password(password, user["password_hash"], user["salt"]):
            return user
        return None

    def list_users(self, role=None, active_only=False):
        sql = "SELECT * FROM users WHERE 1=1"
        params = []
        if role:
            sql += " AND role=?"
            params.append(role)
        if active_only:
            sql += " AND active=1"
        sql += " ORDER BY full_name"
        return self.query(sql, params)

    def add_user(self, username, full_name, role, password, phone=""):
        h, s = hash_password(password)
        return self.execute(
            "INSERT INTO users(username, full_name, phone, role, password_hash, salt, must_change) "
            "VALUES (?, ?, ?, ?, ?, ?, 1)", (username.strip(), full_name.strip(), phone, role, h, s))

    def update_user(self, user_id, full_name, role, phone, active):
        self.execute("UPDATE users SET full_name=?, role=?, phone=?, active=? WHERE id=?",
                     (full_name, role, phone, int(active), user_id))

    def set_password(self, user_id, password, must_change=False):
        h, s = hash_password(password)
        self.execute("UPDATE users SET password_hash=?, salt=?, must_change=? WHERE id=?",
                     (h, s, int(must_change), user_id))

    def delete_user(self, user_id):
        self.execute("DELETE FROM users WHERE id=?", (user_id,))

    def count_admins(self):
        return self.query_one(
            "SELECT COUNT(*) AS n FROM users WHERE role='admin' AND active=1")["n"]

    # ------------------------------------------------------------------
    # Classes & subjects
    # ------------------------------------------------------------------
    def list_classes(self):
        return self.query(
            "SELECT c.*, u.full_name AS form_teacher, "
            "(SELECT COUNT(*) FROM students s WHERE s.class_id=c.id AND s.status='Active') AS student_count "
            "FROM classes c LEFT JOIN users u ON u.id=c.form_teacher_id "
            "ORDER BY c.section, c.name")

    def get_class(self, class_id):
        return self.query_one("SELECT * FROM classes WHERE id=?", (class_id,))

    def add_class(self, name, section, form_teacher_id=None):
        return self.execute("INSERT INTO classes(name, section, form_teacher_id) VALUES (?, ?, ?)",
                            (name.strip(), section, form_teacher_id))

    def update_class(self, class_id, name, section, form_teacher_id):
        self.execute("UPDATE classes SET name=?, section=?, form_teacher_id=? WHERE id=?",
                     (name.strip(), section, form_teacher_id, class_id))

    def delete_class(self, class_id):
        self.execute("DELETE FROM classes WHERE id=?", (class_id,))

    def list_subjects(self, section=None):
        if section:
            return self.query("SELECT * FROM subjects WHERE section=? ORDER BY name", (section,))
        return self.query("SELECT * FROM subjects ORDER BY section, name")

    def add_subject(self, name, section):
        return self.execute("INSERT INTO subjects(name, section) VALUES (?, ?)",
                            (name.strip(), section))

    def delete_subject(self, subject_id):
        self.execute("DELETE FROM subjects WHERE id=?", (subject_id,))

    def class_subjects(self, class_id):
        return self.query(
            "SELECT cs.id, cs.class_id, cs.subject_id, cs.teacher_id, s.name AS subject, "
            "u.full_name AS teacher FROM class_subjects cs "
            "JOIN subjects s ON s.id=cs.subject_id "
            "LEFT JOIN users u ON u.id=cs.teacher_id "
            "WHERE cs.class_id=? ORDER BY s.name", (class_id,))

    def add_class_subject(self, class_id, subject_id, teacher_id=None):
        self.execute("INSERT OR IGNORE INTO class_subjects(class_id, subject_id, teacher_id) "
                     "VALUES (?, ?, ?)", (class_id, subject_id, teacher_id))

    def set_class_subject_teacher(self, cs_id, teacher_id):
        self.execute("UPDATE class_subjects SET teacher_id=? WHERE id=?", (teacher_id, cs_id))

    def remove_class_subject(self, cs_id):
        self.execute("DELETE FROM class_subjects WHERE id=?", (cs_id,))

    def teacher_assignments(self, user):
        """Class/subject pairs a user may enter scores for."""
        base = ("SELECT cs.id, cs.class_id, cs.subject_id, c.name AS class_name, c.section, "
                "s.name AS subject FROM class_subjects cs "
                "JOIN classes c ON c.id=cs.class_id JOIN subjects s ON s.id=cs.subject_id ")
        if user["role"] == "admin":
            return self.query(base + "ORDER BY c.name, s.name")
        return self.query(base + "WHERE cs.teacher_id=? ORDER BY c.name, s.name", (user["id"],))

    def form_classes(self, user):
        """Classes whose results/remarks a user may handle."""
        if user["role"] == "admin":
            return self.list_classes()
        return self.query("SELECT c.*, '' AS form_teacher FROM classes c "
                          "WHERE form_teacher_id=? ORDER BY name", (user["id"],))

    # ------------------------------------------------------------------
    # Students
    # ------------------------------------------------------------------
    STUDENT_FIELDS = ["admission_no", "surname", "first_name", "other_name", "gender",
                      "date_of_birth", "class_id", "guardian_name", "guardian_phone",
                      "address", "state_of_origin", "lga", "religion", "photo_path",
                      "date_admitted", "status"]

    def list_students(self, class_id=None, search="", status="Active"):
        sql = ("SELECT s.*, c.name AS class_name FROM students s "
               "LEFT JOIN classes c ON c.id=s.class_id WHERE 1=1")
        params = []
        if class_id:
            sql += " AND s.class_id=?"
            params.append(class_id)
        if status:
            sql += " AND s.status=?"
            params.append(status)
        if search:
            like = f"%{search.strip()}%"
            sql += (" AND (s.surname LIKE ? OR s.first_name LIKE ? OR s.other_name LIKE ? "
                    "OR s.admission_no LIKE ?)")
            params += [like, like, like, like]
        sql += " ORDER BY s.surname, s.first_name"
        return self.query(sql, params)

    def get_student(self, student_id):
        return self.query_one("SELECT s.*, c.name AS class_name FROM students s "
                              "LEFT JOIN classes c ON c.id=s.class_id WHERE s.id=?", (student_id,))

    def save_student(self, data, student_id=None):
        values = [data.get(f, "") for f in self.STUDENT_FIELDS]
        if student_id:
            sets = ", ".join(f"{f}=?" for f in self.STUDENT_FIELDS)
            self.execute(f"UPDATE students SET {sets} WHERE id=?", values + [student_id])
            return student_id
        cols = ", ".join(self.STUDENT_FIELDS)
        marks = ", ".join("?" for _ in self.STUDENT_FIELDS)
        return self.execute(f"INSERT INTO students({cols}) VALUES ({marks})", values)

    def delete_student(self, student_id):
        self.execute("DELETE FROM students WHERE id=?", (student_id,))

    def next_admission_no(self):
        year = datetime.now().year
        prefix = f"{year}/"
        rows = self.query("SELECT admission_no FROM students WHERE admission_no LIKE ?",
                          (prefix + "%",))
        highest = 0
        for r in rows:
            try:
                highest = max(highest, int(r["admission_no"].split("/")[-1]))
            except ValueError:
                pass
        return f"{prefix}{highest + 1:04d}"

    # ------------------------------------------------------------------
    # Scores
    # ------------------------------------------------------------------
    def get_scores(self, class_id, subject_id, session, term):
        """All active students in a class with their scores for one subject."""
        return self.query(
            "SELECT st.id AS student_id, st.admission_no, "
            "st.surname || ' ' || st.first_name || CASE WHEN st.other_name <> '' "
            "  THEN ' ' || st.other_name ELSE '' END AS name, "
            "sc.ca1, sc.ca2, sc.exam FROM students st "
            "LEFT JOIN scores sc ON sc.student_id=st.id AND sc.subject_id=? "
            "  AND sc.session=? AND sc.term=? "
            "WHERE st.class_id=? AND st.status='Active' "
            "ORDER BY st.surname, st.first_name",
            (subject_id, session, term, class_id))

    def save_score(self, student_id, class_id, subject_id, session, term, ca1, ca2, exam, user_id):
        if ca1 is None and ca2 is None and exam is None:
            self.conn.execute("DELETE FROM scores WHERE student_id=? AND subject_id=? "
                              "AND session=? AND term=?", (student_id, subject_id, session, term))
            return
        self.conn.execute(
            "INSERT INTO scores(student_id, class_id, subject_id, session, term, ca1, ca2, exam, "
            "entered_by, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(student_id, subject_id, session, term) DO UPDATE SET "
            "class_id=excluded.class_id, ca1=excluded.ca1, ca2=excluded.ca2, exam=excluded.exam, "
            "entered_by=excluded.entered_by, updated_at=excluded.updated_at",
            (student_id, class_id, subject_id, session, term, ca1, ca2, exam, user_id,
             datetime.now().isoformat(timespec="seconds")))

    def commit(self):
        self.conn.commit()

    def class_scores(self, class_id, session, term):
        """Every score row for a class in a term (used to build results)."""
        return self.query(
            "SELECT sc.student_id, sc.subject_id, sub.name AS subject, sc.ca1, sc.ca2, sc.exam "
            "FROM scores sc JOIN subjects sub ON sub.id=sc.subject_id "
            "WHERE sc.class_id=? AND sc.session=? AND sc.term=?", (class_id, session, term))

    def student_term_totals(self, student_id, session):
        """Subject totals for each term of a session (for the cumulative column)."""
        return self.query(
            "SELECT subject_id, term, COALESCE(ca1,0)+COALESCE(ca2,0)+COALESCE(exam,0) AS total "
            "FROM scores WHERE student_id=? AND session=?", (student_id, session))

    def list_sessions(self):
        rows = self.query("SELECT DISTINCT session FROM scores ORDER BY session DESC")
        sessions = [r["session"] for r in rows]
        current = self.get_setting("current_session")
        if current and current not in sessions:
            sessions.insert(0, current)
        return sessions

    # ------------------------------------------------------------------
    # Term reports (attendance and comments)
    # ------------------------------------------------------------------
    def get_term_reports(self, class_id, session, term):
        return self.query(
            "SELECT st.id AS student_id, st.admission_no, "
            "st.surname || ' ' || st.first_name AS name, "
            "tr.days_present, tr.teacher_comment, tr.principal_comment "
            "FROM students st LEFT JOIN term_reports tr ON tr.student_id=st.id "
            "  AND tr.session=? AND tr.term=? "
            "WHERE st.class_id=? AND st.status='Active' ORDER BY st.surname, st.first_name",
            (session, term, class_id))

    def get_term_report(self, student_id, session, term):
        return self.query_one("SELECT * FROM term_reports WHERE student_id=? AND session=? "
                              "AND term=?", (student_id, session, term)) or {}

    def save_term_report(self, student_id, class_id, session, term,
                         days_present, teacher_comment, principal_comment):
        self.conn.execute(
            "INSERT INTO term_reports(student_id, class_id, session, term, days_present, "
            "teacher_comment, principal_comment) VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(student_id, session, term) DO UPDATE SET class_id=excluded.class_id, "
            "days_present=excluded.days_present, teacher_comment=excluded.teacher_comment, "
            "principal_comment=excluded.principal_comment",
            (student_id, class_id, session, term, days_present, teacher_comment, principal_comment))

    # ------------------------------------------------------------------
    # Grading scales
    # ------------------------------------------------------------------
    def grade_scale(self, section):
        return self.query("SELECT * FROM grade_scales WHERE section=? ORDER BY min_score DESC",
                          (section,))

    def replace_grade_scale(self, section, rows):
        self.conn.execute("DELETE FROM grade_scales WHERE section=?", (section,))
        for r in rows:
            self.conn.execute(
                "INSERT INTO grade_scales(section, min_score, max_score, grade, remark) "
                "VALUES (?, ?, ?, ?, ?)",
                (section, r["min_score"], r["max_score"], r["grade"], r["remark"]))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Dashboard numbers
    # ------------------------------------------------------------------
    def stats(self):
        one = lambda sql: self.query_one(sql)["n"]
        return {
            "students": one("SELECT COUNT(*) AS n FROM students WHERE status='Active'"),
            "classes": one("SELECT COUNT(*) AS n FROM classes"),
            "teachers": one("SELECT COUNT(*) AS n FROM users WHERE role='teacher' AND active=1"),
            "subjects": one("SELECT COUNT(*) AS n FROM subjects"),
        }
