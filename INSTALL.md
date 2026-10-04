# Installation Guide — Techmiary School Result Manager

By **Techmiary Technology Concept** · [www.techmiary.tech](https://www.techmiary.tech)

This guide explains how to download, install, upgrade and remove Techmiary School
Result Manager on **Windows** and **Linux**.

---

## Contents

1. [System requirements](#1-system-requirements)
2. [Download](#2-download)
3. [Install on Windows](#3-install-on-windows)
4. [Install on Linux](#4-install-on-linux)
5. [First login](#5-first-login)
6. [Upgrading to a new version](#6-upgrading-to-a-new-version)
7. [Where your data is kept, and backups](#7-where-your-data-is-kept-and-backups)
8. [Uninstalling](#8-uninstalling)
9. [Troubleshooting](#9-troubleshooting)
10. [Support](#10-support)

---

## 1. System requirements

| | Windows | Linux |
|---|---|---|
| System | Windows 7 SP1, 8, 8.1, 10 or 11 (32-bit or 64-bit) | 64-bit Ubuntu 22.04 or newer, Linux Mint 21+, Zorin OS 17+, Debian 12+ (other modern distributions also work) |
| Memory | 4 GB RAM recommended | 4 GB RAM recommended |
| Disk space | About 300 MB | About 300 MB |
| Internet | Only to download the program | Only to download the program |
| Printer | Optional: for printing result sheets (you can also save to PDF) | Optional |

The program works fully **offline** once installed.

---

## 2. Download

Open **https://github.com/Dev-Samuel-Jeremiah/techmiary-school-result-manager** and
use the **Download** table, or click **Releases** on the right side of the page and
look under **Assets**.

| File | For |
|---|---|
| `TechmiarySchoolResultManager-Setup-Windows.exe` | Windows: installer (recommended) |
| `TechmiarySchoolResultManager-Portable-Windows.exe` | Windows: runs without installing (e.g. from a flash drive) |
| `techmiary-school-result-manager_amd64.deb` | Ubuntu, Linux Mint, Zorin OS, Debian: installer (recommended) |
| `TechmiarySchoolResultManager-Linux-x86_64` | Any Linux: runs without installing |
| `TechmiarySchoolResultManager-Linux-x64.tar.gz` | Any Linux: installs for one user without an admin password |

You do not need a GitHub account to download.

---

## 3. Install on Windows

### Option A: Setup installer (recommended)

1. Download **`TechmiarySchoolResultManager-Setup-Windows.exe`**.
2. Open your **Downloads** folder and double-click the file.
3. If a blue box says **"Windows protected your PC"**, click **More info**, then
   **Run anyway**. This message appears for new programs that are not code-signed.
4. If Windows asks **"Do you want to allow this app to make changes?"**, click **Yes**.
5. Follow the steps: click **Next**, tick **Create a desktop shortcut** if you want one,
   then click **Install**.
6. Click **Finish**. The program opens.

Afterwards, open it from the **Desktop shortcut** or the **Start menu**
(search for *Techmiary*).

### Option B: Portable (no installation)

1. Download **`TechmiarySchoolResultManager-Portable-Windows.exe`**.
2. Copy it anywhere, for example your Desktop or a flash drive.
3. Double-click it to run. If you see "Windows protected your PC", click
   **More info › Run anyway**.

The portable version takes a few seconds longer to start than the installed version.

---

## 4. Install on Linux

### Option A: .deb package (Ubuntu, Linux Mint, Zorin OS, Debian) — recommended

1. Download **`techmiary-school-result-manager_amd64.deb`**.
2. Open your **Downloads** folder, right-click an empty space and choose
   **Open in Terminal**.
3. Type this command and press **Enter**:

   ```bash
   sudo apt install ./techmiary-school-result-manager_amd64.deb
   ```

4. Type your computer password and press **Enter**. Nothing appears on screen while you
   type the password; this is normal. If asked *"Do you want to continue?"*, press **Y**.
5. Open the **applications menu** and search for **Techmiary School Result Manager**.
   Right-click it and choose **Add to Favorites** to pin it.

On many systems you can also double-click the `.deb` file and click **Install** in the
Software app.

### Option B: Standalone program (any Linux, no installation)

1. Download **`TechmiarySchoolResultManager-Linux-x86_64`**.
2. Right-click the file › **Properties** › **Permissions**, and turn on
   **Allow executing file as program**.
3. Double-click the file to run it.

   If double-clicking does not start it, open a terminal in that folder and run:

   ```bash
   chmod +x TechmiarySchoolResultManager-Linux-x86_64
   ./TechmiarySchoolResultManager-Linux-x86_64
   ```

### Option C: .tar.gz (any Linux, no admin password)

1. Download **`TechmiarySchoolResultManager-Linux-x64.tar.gz`**.
2. Right-click it and choose **Extract Here**.
3. Open the extracted folder, right-click an empty space, choose **Open in Terminal**
   and run:

   ```bash
   ./install.sh
   ```

4. The program is added to your applications menu and your Desktop.
   If the Desktop icon shows a warning, right-click it and choose **Allow Launching**.

---

## 5. First login

| Username | Password |
|---|---|
| `admin` | `admin123` |

You will be asked to choose a new password straight away. **Write it down and keep it
safe** — it is the administrator account.

Suggested first steps:

1. **Settings:** enter the school name, address, motto and logo; set the current session
   and term, and check the score maximums and grading scale.
2. **Classes & Subjects:** create the classes and choose each class's subjects.
3. **Staff Accounts:** create an account for each teacher and assign them to their
   subjects and classes.
4. **Students:** register the students.

---

## 6. Upgrading to a new version

Your school's data is stored separately from the program, so upgrading **does not
delete** students, scores or settings. Still, make a backup first (see section 7).

- **Windows:** download the new `Setup` file and run it. It replaces the old version.
- **Linux (.deb):** download the new `.deb` and run the same
  `sudo apt install ./techmiary-school-result-manager_amd64.deb` command.
- **Linux (.tar.gz):** extract the new version and run `./install.sh` again.
- **Portable / standalone:** delete the old file and use the new one.

To see which version you have, open **Help › About**. The version number is also shown
in the footer at the bottom of the window.

---

## 7. Where your data is kept, and backups

All data (database, student photos and school logo) is kept in one folder:

| System | Folder |
|---|---|
| Windows | `%APPDATA%\TechmiarySchoolResultManager\` (paste this into File Explorer's address bar) |
| Linux | `~/.local/share/TechmiarySchoolResultManager/` (press Ctrl+H in the file manager to see hidden folders) |

You can also find it from **File › Open Data Folder Location** (administrator only).

**Back up often**, especially before an upgrade and at the end of each term:

1. Log in as administrator.
2. Choose **File › Back Up Database...** and save the file.
3. Copy the backup to a flash drive or online storage (Google Drive, email, etc.).

To restore, use **File › Restore From Backup...**. Restoring **replaces** all current
data with the backup.

**Moving to a new computer:** install the program on the new computer, then restore
your latest backup there. Student photos and the logo are not inside the backup file;
to keep them, also copy the `photos` folder and the logo from the data folder above
into the same folder on the new computer.

---

## 8. Uninstalling

Uninstalling removes the program only. The school's data folder (section 7) is kept,
so you can reinstall later without losing anything. Delete that folder yourself only if
you really want to erase all data.

- **Windows:** **Settings › Apps › Installed apps**, find *Techmiary School Result
  Manager*, click **⋯ › Uninstall**. (Or use *Uninstall* in its Start menu folder.)
- **Linux (.deb):**

  ```bash
  sudo apt remove techmiary-school-result-manager
  ```

- **Linux (.tar.gz):** open the extracted folder in a terminal and run `./uninstall.sh`.
- **Portable / standalone:** delete the file.

---

## 9. Troubleshooting

| Problem | Solution |
|---|---|
| Windows: "Windows protected your PC" | Click **More info › Run anyway**. |
| Windows 7: error mentioning `api-ms-win-crt-runtime` or `ucrtbase.dll` | Install Windows update **KB2999226** ("Update for Universal C Runtime") from Microsoft, or run Windows Update, then try again. |
| Windows 7: Setup says it needs a newer Windows | Install **Service Pack 1** through Windows Update. |
| Windows: antivirus blocks or deletes the file | Add the file to your antivirus' allowed list, or download again and choose "Keep" / "Allow". |
| Linux: program does not open | Open a terminal and run `sudo apt install libxcb-cursor0`, then try again. |
| Linux: "Permission denied" | Run `chmod +x` on the file (see section 4, Option B). |
| Linux: `.deb` double-click opens an archive manager | Use the terminal command in section 4, Option A. |
| Forgot the admin password | Ask Techmiary support (section 10). Restoring an older backup also restores the password that was in use then. |
| Result sheet prints too large or cut off | In the print settings, choose **A4** paper and 100% scale. |
| "An unexpected error occurred" | Details are saved in `error.log` in the data folder (section 7). Send that file to support. |

---

## 10. Support

**Techmiary Technology Concept** — website: [www.techmiary.tech](https://www.techmiary.tech)

When asking for help, please include your Windows or Linux version, the program version
(**Help › About**), and a screenshot of any error message.

---
© Techmiary Technology Concept · www.techmiary.tech
