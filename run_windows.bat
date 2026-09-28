@echo off
REM Run Techmiary School Result Manager from source on Windows (for testing changes).
REM First time: installs PySide6 (needs internet once).
cd /d "%~dp0"
python -c "import PySide6" 2>NUL || python -m pip install -r requirements.txt
python app\main.py
pause
