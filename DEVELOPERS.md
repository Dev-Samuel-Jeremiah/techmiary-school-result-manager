# Techmiary School Result Manager — Developer guide

By **Techmiary Technology Concept** · www.techmiary.tech

This is the editable program. Change the code here, then rebuild to produce new installers.

## What it does

- **Students**: register students with passport photo, class, gender, date of birth, guardian details, state/LGA and address. You can search, edit, move or promote students to another class, and mark them Graduated or Left.
- **Classes & Subjects**: create classes (Primary or Secondary), choose each class's subjects, assign a subject teacher to each subject and a class teacher to each class.
- **Staff accounts**: the admin creates accounts for teachers. Each teacher sees only the subjects assigned to them.
- **Enter Scores**: CA 1, CA 2 and Exam are typed into a grid. The total and grade are worked out as you type, and pressing Enter moves to the next student. You can also paste a column copied from Excel.
- **Remarks & Attendance**: class teachers enter days present and a comment for each student. The admin adds the principal's or head teacher's comment. Empty comments can be auto-filled.
- **Results**: totals, averages, subject position, class position (ties share a place), class average, and highest and lowest score per subject. In the 2nd and 3rd term the sheet also shows earlier term totals and a cumulative average.
- **Printing**: preview and print one student, selected students or a whole class (one A4 page per student). You can also save a whole class to PDF or print a class broadsheet.
- **Settings**: school name, address, motto and logo; current session and term; next-term date; score maximums (default 20/20/60); and editable grading scales (Secondary A1–F9, Primary A–F).
- **Backup and restore** are under the File menu.


## Test your changes (no build needed)

- **Windows:** double-click `run_windows.bat`
- **Linux:** `./run_linux.sh`

First login: username `admin`, password `admin123` (you must change it straight away).

## Releasing an upgrade

1. Make your changes in `app/`.
2. Open `app/branding.py` and raise `APP_VERSION` (for example `1.1.0` → `1.2.0`).
3. Build:
   - **Windows:** double-click `build_windows.bat` (on a Windows 10/11 PC with
     [Python 3.8.10 32-bit](https://www.python.org/ftp/python/3.8.10/python-3.8.10.exe) installed)
   - **Linux:** run `./build_linux.sh` (on a Linux PC)
4. Give schools the new files from the `Installers` folder. Running the new
   Setup.exe (or .deb) upgrades the program in place; their data is kept.

Never change the `AppId` line in `installer/windows_installer.iss`, or Windows will
treat the new version as a different program instead of an upgrade.

### Publishing a new version on GitHub

The repository builds the installers by itself (see `.github/workflows/build-installers.yml`):

1. Raise `APP_VERSION` in `app/branding.py` and upload your changes.
2. On GitHub open **Releases › Draft a new release**, create a tag such as `v1.2.0`
   (same number as `APP_VERSION`), write what changed, and click **Publish release**.
3. About 10–15 minutes later the Windows and Linux installers are attached to that release,
   and the download links in `README.md` point to them automatically.

To test a build without publishing, open **Actions › Build installers › Run workflow**
and download the results from the run page.

## Why the Windows build uses Python 3.8 and Qt 5

Qt 6 (PySide6) and Python 3.9+ only run on Windows 10/11. To support Windows 7, 8 and
8.1 as well, the Windows program is built with **Python 3.8 (32-bit)** and **Qt 5.15
(PySide2)** — pinned in `requirements-windows.txt`. A 32-bit program runs on both 32-bit
and 64-bit Windows, so one installer covers every PC. Linux uses Qt 6.

The code works with both because every screen imports Qt through **QtPy**
(`from qtpy.QtWidgets import ...`, never `from PySide6...`), and `app/qt_compat.py`
fills the small gaps. Keep it that way when you add new code, and keep new code
Python 3.8-compatible (e.g. no `match`, no `list[int]` type hints, no `str | None`).

Both build scripts first run `tools/smoke_test.py`, which opens every screen and prints
sample results to PDF; the build stops if anything fails.

## Changing the name or company details

Everything is in `app/branding.py`: product name, company name, website, version,
.exe name and data-folder name. The footer at the bottom of every screen, the login
window, the About box and the line at the foot of printed result sheets all read from it.

## Where the data is stored

- Windows: `%APPDATA%\TechmiarySchoolResultManager\`
- Linux: `~/.local/share/TechmiarySchoolResultManager/`

If a PC still has data from the old "School Result Manager", it is copied into the new
folder automatically the first time the program opens (the old folder is left untouched).
Use **File › Back Up Database** often and keep copies on a flash drive.

## Suggested order for a new term

1. **Settings:** set the session and term, next-term date and times school opened.
2. Teachers enter scores under **Enter Scores**.
3. Class teachers fill in **Remarks & Attendance**.
4. The admin adds principal comments, then prints from **Results**.


## Project files

| File | What it contains |
|---|---|
| `app/branding.py` | **Product name, company name, website and version number** |
| `app/qt_compat.py` | Lets the code run on Qt 5 (Windows 7/8) and Qt 6 |
| `app/main.py` | Starts the program, login and main window |
| `app/database.py` | Database tables, default grading and subjects |
| `app/results.py` | Totals, grades and positions, and the result sheet layout |
| `app/pages_admin.py` | Dashboard, Students, Classes, Staff and Settings screens |
| `app/pages_results.py` | Enter Scores, Remarks and Results screens |
| `app/ui_dialogs.py` | Pop-up forms (login, student form, etc.) |
| `app/ui_common.py` | Colours, table helpers and printing |

To change how the printed result looks, edit `student_sheet_html()` in `app/results.py`.
| `build_windows.bat` / `build_linux.sh` | Build the installers |
| `installer/windows_installer.iss` | Windows Setup.exe settings (Inno Setup) |
| `installer/linux/` | Linux install/uninstall scripts |
| `tools/make_version_info.py` | Puts company/version details into the .exe |
| `tools/smoke_test.py` | Automatic self-test run before every build |
| `requirements-windows.txt` | Pinned versions for the Windows 7–11 build |
| `.github/workflows/build-installers.yml` | Automatic builds on GitHub |
