@echo off
setlocal EnableExtensions
REM =========================================================================
REM  Techmiary School Result Manager - Windows build
REM  Double-click this file ON A WINDOWS PC (needs internet the first time).
REM
REM  It produces, in the "Installers\Windows" folder:
REM    1. TechmiarySchoolResultManager-Setup-<version>.exe   (installer: double-click
REM       to install, adds Start Menu + Desktop shortcut and an uninstaller)
REM    2. TechmiarySchoolResultManager-Portable-<version>.exe (single file, runs
REM       without installing - good for a flash drive)
REM
REM  Needs: Python 3.9-3.12 from https://www.python.org ("Add Python to PATH" ticked)
REM  Inno Setup 6 is installed automatically with winget if it is missing.
REM =========================================================================
cd /d "%~dp0"

set "OUTDIR=%OUTPUT_DIR%"
if "%OUTDIR%"=="" set "OUTDIR=%~dp0..\Installers\Windows"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

REM ---- 1. Find Python -------------------------------------------------------
set "PY="
where py >NUL 2>&1 && set "PY=py -3"
if "%PY%"=="" where python >NUL 2>&1 && set "PY=python"
if "%PY%"=="" (
  echo Python was not found. Install it from https://www.python.org and tick "Add Python to PATH".
  pause & exit /b 1
)

REM ---- 2. Private build environment -----------------------------------------
if not exist ".venv-build\Scripts\python.exe" (
  echo Creating build environment...
  %PY% -m venv .venv-build || (echo Could not create the build environment. & pause & exit /b 1)
)
set "VPY=%~dp0.venv-build\Scripts\python.exe"
"%VPY%" -m pip install --upgrade pip
"%VPY%" -m pip install -r requirements.txt pyinstaller || (echo Package install failed - check your internet. & pause & exit /b 1)

REM ---- 3. Read name and version from app\branding.py -------------------------
for /f "delims=" %%v in ('"%VPY%" tools\make_version_info.py get VERSION') do set "VER=%%v"
for /f "delims=" %%v in ('"%VPY%" tools\make_version_info.py get EXE') do set "EXE=%%v"
"%VPY%" tools\make_version_info.py
echo Building %EXE% version %VER% ...

REM ---- 4. Program folder (used by the installer) ----------------------------
"%VPY%" -m PyInstaller --noconfirm --clean --windowed ^
  --name "%EXE%" ^
  --icon app\icon.ico ^
  --version-file build\version_info.txt ^
  --add-data "app\icon.png;." ^
  --paths app ^
  app\main.py || (echo PyInstaller build failed. & pause & exit /b 1)

REM ---- 5. Portable single-file .exe -----------------------------------------
"%VPY%" -m PyInstaller --noconfirm --onefile --windowed ^
  --name "%EXE%-Portable-%VER%" ^
  --icon app\icon.ico ^
  --version-file build\version_info.txt ^
  --add-data "app\icon.png;." ^
  --paths app ^
  --distpath build\portable ^
  --workpath build\portable-work ^
  app\main.py || (echo Portable build failed. & pause & exit /b 1)
copy /Y "build\portable\%EXE%-Portable-%VER%.exe" "%OUTDIR%\" >NUL

REM ---- 6. Setup.exe installer (Inno Setup) ----------------------------------
call :find_iscc
if "%ISCC%"=="" (
  echo Inno Setup not found - installing it with winget...
  winget install --id JRSoftware.InnoSetup -e --silent --accept-package-agreements --accept-source-agreements
  call :find_iscc
)
if "%ISCC%"=="" (
  echo.
  echo Could not find Inno Setup. Install it from https://jrsoftware.org/isdl.php
  echo then run this file again. The portable .exe is already in:
  echo   %OUTDIR%
  pause & exit /b 1
)
"%ISCC%" /Qp /DMyAppVersion=%VER% "/DOutputDir=%OUTDIR%" installer\windows_installer.iss || (echo Installer build failed. & pause & exit /b 1)

echo.
echo =====================================================================
echo  Done. Your Windows files are in:
echo    %OUTDIR%
echo    - %EXE%-Setup-%VER%.exe     (double-click to install)
echo    - %EXE%-Portable-%VER%.exe  (runs without installing)
echo =====================================================================
if "%CI%"=="" pause
exit /b 0

:find_iscc
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
exit /b 0
