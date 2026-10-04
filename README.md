# Techmiary School Result Manager

Desktop software for primary and secondary schools: register students, enter CA and
exam scores, and print term result sheets with positions, averages and comments.
Works offline on **Windows** and **Linux**.

By **Techmiary Technology Concept** · [www.techmiary.tech](https://www.techmiary.tech)

## ⬇️ Download

| System | Download | How to install |
|---|---|---|
| **Windows 7, 8, 8.1, 10, 11** | [**Setup (recommended)**](../../releases/latest/download/TechmiarySchoolResultManager-Setup-Windows.exe) | Double-click and follow the steps |
| Windows (no install) | [Portable .exe](../../releases/latest/download/TechmiarySchoolResultManager-Portable-Windows.exe) | Just double-click to run; good for a flash drive |
| **Ubuntu / Debian / Mint / Zorin** | [**.deb package**](../../releases/latest/download/techmiary-school-result-manager_amd64.deb) | Double-click and choose *Install* |
| Any Linux | [Standalone program](../../releases/latest/download/TechmiarySchoolResultManager-Linux-x86_64) | Right-click › Properties › allow executing, then double-click |
| Any Linux | [.tar.gz](../../releases/latest/download/TechmiarySchoolResultManager-Linux-x64.tar.gz) | Extract, then run `./install.sh` |

All versions: see the [Releases page](../../releases).

📘 **Step-by-step instructions:** [Installation Guide](INSTALL.md)

**First login:** username `admin`, password `admin123`. You'll be asked to change it straight away.

### Notes

- **Windows "Windows protected your PC" message:** click **More info › Run anyway**. It
  appears for new programs that aren't code-signed.
- **Upgrading:** download and run the newest Setup (or .deb). The school's data is kept.
- **Linux, program won't open:** run `sudo apt install libxcb-cursor0`.
- **Back up** often: *File › Back Up Database*, and keep copies on a flash drive.

## Features

- Student registration with passport photo, guardian details, promotion and graduation
- Classes and subjects, subject teachers and class teachers
- Teacher accounts: each teacher sees only their own subjects
- Score entry grid (CA 1, CA 2, Exam) with totals and grades as you type
- Remarks, attendance, principal/head-teacher comments
- Positions (ties share a place), class averages, cumulative results for 2nd and 3rd term
- Print or save to PDF: single student, selected students, whole class, broadsheet
- Editable grading scales and score maximums; backup and restore

## For developers

See [DEVELOPERS.md](DEVELOPERS.md) for running from source, making changes and
publishing a new version.

---
© Techmiary Technology Concept · [www.techmiary.tech](https://www.techmiary.tech)
