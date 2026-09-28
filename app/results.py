"""
results.py - Works out totals, grades and positions, and builds the
printable result sheet (as HTML that Qt can print or save to PDF).

This file does not use Qt, so it can be tested on its own.
"""

import html
import os
from pathlib import Path

from branding import COMPANY_WEBSITE, PRODUCT_NAME
from database import TERMS


# ----------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------
def ordinal(n):
    if n is None:
        return "-"
    n = int(n)
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def fmt(value, decimals=1):
    """Show 12.0 as 12 and 12.5 as 12.5; blanks as '-'."""
    if value is None or value == "":
        return "-"
    value = round(float(value), decimals)
    if value == int(value):
        return str(int(value))
    return f"{value:.{decimals}f}"


def grade_for(score, scale):
    """Return (grade, remark) for a score using a grade scale list."""
    if score is None:
        return "-", "-"
    for row in scale:  # scale is sorted highest first
        if row["min_score"] <= round(score, 2) <= row["max_score"] + 0.0001:
            return row["grade"], row["remark"]
    # Score falls in a gap of the scale: use the closest lower band
    for row in scale:
        if score >= row["min_score"]:
            return row["grade"], row["remark"]
    return (scale[-1]["grade"], scale[-1]["remark"]) if scale else ("-", "-")


def rank(values):
    """values: {key: number}. Returns {key: position}; ties share a position
    (e.g. 1st, 2nd, 2nd, 4th)."""
    ordered = sorted(values.items(), key=lambda kv: kv[1], reverse=True)
    positions = {}
    last_value, last_pos = None, 0
    for index, (key, value) in enumerate(ordered, start=1):
        if value != last_value:
            last_pos = index
            last_value = value
        positions[key] = last_pos
    return positions


def suggest_comment(average, role="teacher"):
    """Automatic comment ideas based on the student's average."""
    if average is None:
        return ""
    if role == "teacher":
        if average >= 75:
            return "An excellent performance. Keep it up!"
        if average >= 65:
            return "A very good result. Aim higher next term."
        if average >= 50:
            return "A good effort, but there is room for improvement."
        if average >= 40:
            return "Fair result. Needs to work harder."
        return "Poor performance. Must sit up and work much harder."
    if average >= 75:
        return "Outstanding result. Well done."
    if average >= 65:
        return "Very good. Keep working hard."
    if average >= 50:
        return "Good result. You can do better."
    if average >= 40:
        return "Put in more effort next term."
    return "Weak result. Parents should give closer attention."


# ----------------------------------------------------------------------
# Result calculation
# ----------------------------------------------------------------------
def compute_class_results(db, class_id, session, term):
    """Build the full result data for every student in a class.

    Returns a dict:
      {
        "class": {...}, "session": ..., "term": ..., "scale": [...],
        "subjects": [ {subject_id, subject}, ... ],
        "subject_stats": {subject_id: {highest, lowest, average}},
        "students": [ {student..., "rows": [...], "total": .., "average": ..,
                       "position": .., "grade": .., ...}, ... ]   # ordered by name
        "class_size": int,
      }
    """
    klass = db.get_class(class_id)
    if not klass:
        raise ValueError("Class not found")
    scale = db.grade_scale(klass["section"])
    ca1_max, ca2_max, exam_max = db.max_scores()
    students = db.list_students(class_id=class_id)
    offered = db.class_subjects(class_id)

    score_rows = db.class_scores(class_id, session, term)
    # scores[student_id][subject_id] = row
    scores = {}
    subject_names = {c["subject_id"]: c["subject"] for c in offered}
    for r in score_rows:
        scores.setdefault(r["student_id"], {})[r["subject_id"]] = r
        subject_names.setdefault(r["subject_id"], r["subject"])

    # Order subjects: offered ones first (alphabetical), then any extra that have scores
    subject_ids = [c["subject_id"] for c in offered]
    for sid in sorted(subject_names, key=lambda s: subject_names[s]):
        if sid not in subject_ids:
            subject_ids.append(sid)

    student_ids = {s["id"] for s in students}

    # Subject totals per student
    totals = {}  # subject_id -> {student_id: total}
    for st in students:
        for sid, r in scores.get(st["id"], {}).items():
            t = (r["ca1"] or 0) + (r["ca2"] or 0) + (r["exam"] or 0)
            totals.setdefault(sid, {})[st["id"]] = t

    subject_stats = {}
    subject_positions = {}
    for sid, per_student in totals.items():
        vals = [v for k, v in per_student.items() if k in student_ids]
        if vals:
            subject_stats[sid] = {
                "highest": max(vals),
                "lowest": min(vals),
                "average": sum(vals) / len(vals),
            }
            subject_positions[sid] = rank(per_student)

    # Earlier terms (for cumulative columns)
    term_index = TERMS.index(term) if term in TERMS else 0
    previous_terms = TERMS[:term_index]

    results = []
    averages = {}
    for st in students:
        rows = []
        grand_total = 0.0
        taken = 0
        history = {}
        if previous_terms:
            for h in db.student_term_totals(st["id"], session):
                history.setdefault(h["subject_id"], {})[h["term"]] = h["total"]
        for sid in subject_ids:
            r = scores.get(st["id"], {}).get(sid)
            if not r:
                continue
            total = totals[sid][st["id"]]
            g, remark = grade_for(total, scale)
            prev = [history.get(sid, {}).get(t) for t in previous_terms]
            cum_values = [p for p in prev if p is not None] + [total]
            cum_avg = sum(cum_values) / len(cum_values)
            rows.append({
                "subject_id": sid,
                "subject": subject_names.get(sid, "?"),
                "ca1": r["ca1"], "ca2": r["ca2"], "exam": r["exam"],
                "total": total,
                "grade": g, "remark": remark,
                "position": subject_positions.get(sid, {}).get(st["id"]),
                "stats": subject_stats.get(sid, {}),
                "previous": prev,
                "cumulative": cum_avg,
            })
            grand_total += total
            taken += 1
        average = grand_total / taken if taken else None
        if average is not None:
            averages[st["id"]] = round(average, 2)
        g, remark = grade_for(average, scale) if average is not None else ("-", "-")
        results.append(dict(st, rows=rows, total=grand_total, subjects_taken=taken,
                            average=average, grade=g, grade_remark=remark,
                            obtainable=taken * (ca1_max + ca2_max + exam_max)))

    positions = rank(averages)
    for r in results:
        r["position"] = positions.get(r["id"])

    return {
        "class": klass,
        "session": session,
        "term": term,
        "previous_terms": previous_terms,
        "scale": scale,
        "max": (ca1_max, ca2_max, exam_max),
        "subject_stats": subject_stats,
        "students": results,
        "class_size": len(students),
        "class_average": (sum(averages.values()) / len(averages)) if averages else None,
    }


# ----------------------------------------------------------------------
# HTML result sheet
# ----------------------------------------------------------------------
def _e(text):
    return html.escape(str(text if text is not None else ""))


def image_src(path, key, mode):
    """mode 'resource' -> a name Qt looks up via addResource,
    mode 'file' -> a file:// URL (for browsers)."""
    if not path or not os.path.exists(path):
        return None
    if mode == "file":
        return Path(path).resolve().as_uri()
    return key


SHEET_CSS = """
body { font-family: 'Arial', 'Liberation Sans', sans-serif; font-size: 9pt; color: #000; }
td, th { font-size: 9pt; }
.school { font-size: 18pt; font-weight: bold; color: #0b3d91; }
.sub { font-size: 9pt; }
.motto { font-size: 9pt; font-style: italic; }
.title { font-size: 11pt; font-weight: bold; color: #ffffff; background-color: #0b3d91; }
.label { font-weight: bold; background-color: #eef2fa; }
.head { font-weight: bold; background-color: #0b3d91; color: #ffffff; }
.small { font-size: 8pt; }
"""


def student_sheet_html(data, student, settings, image_mode="resource", page_break=False):
    klass = data["class"]
    ca1_max, ca2_max, exam_max = data["max"]
    prev_terms = data["previous_terms"]
    short = {"First Term": "1st Term", "Second Term": "2nd Term", "Third Term": "3rd Term"}
    report = student.get("report") or {}

    logo = image_src(settings.get("logo_path"), "logo", image_mode)
    photo = image_src(student.get("photo_path"), f"photo_{student['id']}", image_mode)

    brk = ' style="page-break-before: always;"' if page_break else ""
    out = []

    # ---- Header -------------------------------------------------------
    out.append(f'<table width="100%" cellspacing="0" cellpadding="2"{brk}><tr>')
    out.append('<td width="15%" align="left" valign="middle">'
               + (f'<img src="{_e(logo)}" width="80" height="80">' if logo else "&nbsp;")
               + "</td>")
    contact = " | ".join(x for x in [settings.get("school_phone", ""),
                                     settings.get("school_email", "")] if x)
    out.append('<td width="70%" align="center" valign="middle">'
               f'<div class="school">{_e(settings.get("school_name", "")).upper()}</div>'
               f'<div class="sub">{_e(settings.get("school_address", ""))}</div>'
               + (f'<div class="sub">{_e(contact)}</div>' if contact else "")
               + (f'<div class="motto">Motto: {_e(settings.get("school_motto"))}</div>'
                  if settings.get("school_motto") else "")
               + "</td>")
    out.append('<td width="15%" align="right" valign="middle">'
               + (f'<img src="{_e(photo)}" width="80" height="90">' if photo else "&nbsp;")
               + "</td></tr></table>")

    out.append('<table width="100%" cellspacing="0" cellpadding="4"><tr>'
               f'<td class="title" align="center">STUDENT\'S REPORT SHEET &mdash; '
               f'{_e(data["term"]).upper()}, {_e(data["session"])} ACADEMIC SESSION</td>'
               "</tr></table><br>")

    # ---- Student information ----------------------------------------
    name = " ".join(x for x in [student["surname"].upper(), student["first_name"],
                                student.get("other_name", "")] if x)
    days_opened = settings.get("days_school_opened", "") or "-"
    days_present = report.get("days_present")
    info = [
        ("Name", name, "Admission No.", student["admission_no"]),
        ("Class", klass["name"], "Gender", student.get("gender") or "-"),
        ("No. in Class", data["class_size"], "Position in Class",
         f'{ordinal(student["position"])} out of {data["class_size"]}'
         if student["position"] else "-"),
        ("Times School Opened", days_opened, "Times Present",
         days_present if days_present not in (None, "") else "-"),
    ]
    out.append('<table width="100%" border="1" cellspacing="0" cellpadding="3" '
               'style="border-collapse: collapse; border-color: #555;">')
    for a, b, c, d in info:
        out.append(f'<tr><td class="label" width="20%">{_e(a)}</td><td width="30%">{_e(b)}</td>'
                   f'<td class="label" width="20%">{_e(c)}</td><td width="30%">{_e(d)}</td></tr>')
    out.append("</table><br>")

    # ---- Subject scores ----------------------------------------------
    heads = ["S/N", "SUBJECT", f"CA 1<br>({fmt(ca1_max)})", f"CA 2<br>({fmt(ca2_max)})",
             f"EXAM<br>({fmt(exam_max)})", f"TOTAL<br>({fmt(ca1_max + ca2_max + exam_max)})"]
    for t in prev_terms:
        heads.append(short.get(t, t).upper())
    if prev_terms:
        heads.append("CUM.<br>AVG")
    heads += ["GRADE", "SUBJ.<br>POS.", "CLASS<br>AVG", "HIGH", "LOW", "REMARK"]

    out.append('<table width="100%" border="1" cellspacing="0" cellpadding="3" '
               'style="border-collapse: collapse; border-color: #555;">')
    out.append("<tr>" + "".join(f'<td class="head" align="center">{h}</td>' for h in heads)
               + "</tr>")
    if not student["rows"]:
        out.append(f'<tr><td colspan="{len(heads)}" align="center">'
                   "No scores have been entered for this student yet.</td></tr>")
    for i, r in enumerate(student["rows"], start=1):
        bg = ' bgcolor="#f6f8fc"' if i % 2 == 0 else ""
        cells = [
            (str(i), "center"), (_e(r["subject"]), "left"),
            (fmt(r["ca1"]), "center"), (fmt(r["ca2"]), "center"), (fmt(r["exam"]), "center"),
            (f"<b>{fmt(r['total'])}</b>", "center"),
        ]
        for p in r["previous"]:
            cells.append((fmt(p), "center"))
        if prev_terms:
            cells.append((fmt(r["cumulative"]), "center"))
        stats = r["stats"]
        cells += [
            (f"<b>{_e(r['grade'])}</b>", "center"),
            (ordinal(r["position"]) if r["position"] else "-", "center"),
            (fmt(stats.get("average")), "center"),
            (fmt(stats.get("highest")), "center"),
            (fmt(stats.get("lowest")), "center"),
            (_e(r["remark"]), "left"),
        ]
        out.append(f"<tr{bg}>" + "".join(f'<td align="{a}">{c}</td>' for c, a in cells) + "</tr>")
    out.append("</table><br>")

    # ---- Summary -----------------------------------------------------
    avg = student["average"]
    out.append('<table width="100%" border="1" cellspacing="0" cellpadding="3" '
               'style="border-collapse: collapse; border-color: #555;"><tr>'
               f'<td class="label">Total Obtained</td><td align="center">{fmt(student["total"])}</td>'
               f'<td class="label">Total Obtainable</td><td align="center">{fmt(student["obtainable"])}</td>'
               f'<td class="label">Average</td><td align="center"><b>{fmt(avg, 2)}%</b></td>'
               f'<td class="label">Overall Grade</td><td align="center"><b>{_e(student["grade"])}</b></td>'
               f'<td class="label">Class Average</td><td align="center">{fmt(data["class_average"], 2)}</td>'
               "</tr></table><br>")

    # ---- Grade key --------------------------------------------------
    def band_top(v):
        return fmt(int(v)) if v - int(v) > 0.5 else fmt(v)
    key = ", &nbsp;".join(
        f'<b>{_e(g["grade"])}</b> = {fmt(g["min_score"])}-{band_top(g["max_score"])} '
        f'({_e(g["remark"])})' for g in data["scale"])
    out.append(f'<p class="small"><b>GRADE KEY:</b> {key}</p>')

    # ---- Comments ---------------------------------------------------
    form_teacher = student.get("form_teacher_name") or ""
    head_title = "Principal" if klass["section"] == "Secondary" else "Head Teacher"
    head_name = settings.get("principal_name" if klass["section"] == "Secondary"
                             else "head_teacher_name", "")
    out.append('<table width="100%" border="1" cellspacing="0" cellpadding="5" '
               'style="border-collapse: collapse; border-color: #555;">')
    out.append(f'<tr><td class="label" width="28%">Class Teacher\'s Comment</td>'
               f'<td>{_e(report.get("teacher_comment") or "")}&nbsp;</td></tr>')
    out.append(f'<tr><td class="label">Class Teacher\'s Name</td>'
               f'<td>{_e(form_teacher)}&nbsp;&nbsp;&nbsp;&nbsp;Signature: ______________________</td></tr>')
    out.append(f'<tr><td class="label">{head_title}\'s Comment</td>'
               f'<td>{_e(report.get("principal_comment") or "")}&nbsp;</td></tr>')
    out.append(f'<tr><td class="label">{head_title}\'s Name</td>'
               f'<td>{_e(head_name)}&nbsp;&nbsp;&nbsp;&nbsp;Signature &amp; Stamp: ______________________</td></tr>')
    if settings.get("next_term_begins"):
        out.append(f'<tr><td class="label">Next Term Begins</td>'
                   f'<td><b>{_e(settings.get("next_term_begins"))}</b></td></tr>')
    out.append("</table>")
    out.append(f'<p class="small" align="center" style="color:#777;">'
               f'Generated with {_e(PRODUCT_NAME)} &middot; {_e(COMPANY_WEBSITE)}</p>')
    return "".join(out)


def build_results_html(db, class_id, session, term, student_ids=None, image_mode="resource"):
    """Return (html, data). Only the listed student_ids are included, if given."""
    data = compute_class_results(db, class_id, session, term)
    settings = db.get_settings()
    klass = data["class"]
    form_teacher = ""
    if klass.get("form_teacher_id"):
        u = db.query_one("SELECT full_name FROM users WHERE id=?", (klass["form_teacher_id"],))
        form_teacher = u["full_name"] if u else ""

    chosen = [s for s in data["students"]
              if student_ids is None or s["id"] in set(student_ids)]
    parts = []
    for i, st in enumerate(chosen):
        st["report"] = db.get_term_report(st["id"], session, term)
        st["form_teacher_name"] = form_teacher
        parts.append(student_sheet_html(data, st, settings, image_mode, page_break=i > 0))
    body = "".join(parts) or "<p>No students selected.</p>"
    doc = (f"<html><head><meta charset='utf-8'><style>{SHEET_CSS}</style></head>"
           f"<body>{body}</body></html>")
    return doc, data


def broadsheet_html(db, class_id, session, term):
    """A one-page summary of the whole class (all subjects, totals, positions)."""
    data = compute_class_results(db, class_id, session, term)
    settings = db.get_settings()
    subjects = []
    seen = set()
    for st in data["students"]:
        for r in st["rows"]:
            if r["subject_id"] not in seen:
                seen.add(r["subject_id"])
                subjects.append((r["subject_id"], r["subject"]))
    subjects.sort(key=lambda s: s[1])

    out = [f"<html><head><meta charset='utf-8'><style>{SHEET_CSS}</style></head><body>",
           f'<p align="center"><span class="school">{_e(settings.get("school_name", "")).upper()}</span><br>'
           f'<b>BROADSHEET &mdash; {_e(data["class"]["name"])} &mdash; {_e(term)}, '
           f'{_e(session)}</b></p>',
           '<table width="100%" border="1" cellspacing="0" cellpadding="2" '
           'style="border-collapse: collapse; border-color: #555;"><tr>',
           '<td class="head">S/N</td><td class="head">ADM. NO</td><td class="head">NAME</td>']
    for _, name in subjects:
        out.append(f'<td class="head" align="center">{_e(name)}</td>')
    out.append('<td class="head">TOTAL</td><td class="head">AVG</td><td class="head">POS.</td></tr>')

    ordered = sorted(data["students"], key=lambda s: (s["position"] is None, s["position"] or 0,
                                                      s["surname"]))
    for i, st in enumerate(ordered, start=1):
        by_subject = {r["subject_id"]: r["total"] for r in st["rows"]}
        out.append(f'<tr><td align="center">{i}</td><td>{_e(st["admission_no"])}</td>'
                   f'<td>{_e(st["surname"].upper())} {_e(st["first_name"])}</td>')
        for sid, _ in subjects:
            out.append(f'<td align="center">{fmt(by_subject.get(sid))}</td>')
        out.append(f'<td align="center"><b>{fmt(st["total"])}</b></td>'
                   f'<td align="center">{fmt(st["average"], 2)}</td>'
                   f'<td align="center">{ordinal(st["position"]) if st["position"] else "-"}</td></tr>')
    out.append("</table>")
    out.append(f'<p class="small" align="center" style="color:#777;">'
               f'Generated with {_e(PRODUCT_NAME)} &middot; {_e(COMPANY_WEBSITE)}</p>')
    out.append("</body></html>")
    return "".join(out)
