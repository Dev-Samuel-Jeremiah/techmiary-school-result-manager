@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM =========================================================================
REM  Techmiary School Result Manager - Windows build
REM
REM  The program it makes runs on Windows 7 SP1, 8, 8.1, 10 and 11,
REM  both 32-bit and 64-bit.
REM
REM  It produces, in the "Installers\Windows" folder:
REM    1. TechmiarySchoolResultManager-Setup-<version>.exe    (installer)
REM    2. TechmiarySchoolResultManager-Portable-<version>.exe (no install needed)
REM
REM  Needs on the build PC (any Windows 10/11 PC, internet the first time):
REM    * Python 3.8 32-bit - the last Python that supports Windows 7/8:
REM        https://www.python.org/ftp/python/3.8.10/python-3.8.10.exe
REM      (It can be installed next to any newer Python you already have.)
REM    * Inno Setup 6 - installed automatically with winget if missing.
REM =========================================================================
cd /d "%~dp0"

set "OUTDIR=%OUTPUT_DIR%"
if "%OUTDIR%"=="" set "OUTDIR=%~dp0..\Installers\Windows"
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

REM ---- 1. Find Python 3.8 (32-bit) ------------------------------------------
REM GitHub's build sets PY_CMD itself; on your own PC the "py" launcher finds it.
set "PY=%PY_CMD%"
if "%PY%"=="" (
  py -3.8-32 -c "import sys" >NUL 2>&1 && set "PY=py -3.8-32"
)
if "%PY%"=="" (
  echo.
  echo Python 3.8 32-bit was not found.
  echo Download and install it from:
  echo   https://www.python.org/ftp/python/3.8.10/python-3.8.10.exe
  echo then run this file again.
  echo.
  echo Why: newer Python and Qt versions do not run on Windows 7 and 8.
  goto :fail
)
%PY% -c "import sys, struct; v=sys.version_info[:2]; b=struct.calcsize('P')*8; print('Using Python %%d.%%d %%d-bit' %% (v[0], v[1], b)); sys.exit(0 if v==(3,8) and b==32 else 1)" || (
  echo This build needs Python 3.8 32-bit, but a different Python was found.
  goto :fail
)

REM ---- 2. Private build environment -----------------------------------------
if not exist ".venv-win\Scripts\python.exe" (
  echo Creating build environment...
  %PY% -m venv .venv-win || (echo Could not create the build environment. & goto :fail)
)
set "VPY=%~dp0.venv-win\Scripts\python.exe"
"%VPY%" -m pip install --upgrade pip
"%VPY%" -m pip install -r requirements-windows.txt || (echo Package install failed - check your internet. & goto :fail)

REM ---- 3. Self-test: open every screen and print to PDF ---------------------
echo.
echo Running self-test...
set "QT_QPA_PLATFORM=offscreen"
"%VPY%" tools\smoke_test.py || (echo SELF-TEST FAILED - nothing was built. & goto :fail)
set "QT_QPA_PLATFORM="

REM ---- 4. Read name and version from app\branding.py -------------------------
for /f "delims=" %%v in ('"%VPY%" tools\make_version_info.py get VERSION') do set "VER=%%v"
for /f "delims=" %%v in ('"%VPY%" tools\make_version_info.py get EXE') do set "EXE=%%v"
"%VPY%" tools\make_version_info.py
echo Building %EXE% version %VER% ...

REM ---- 5. Windows 7 runtime files (Universal C Runtime) ----------------------
REM Windows 10/11 already have these. Windows 7/8 PCs that missed updates do not,
REM so we ship them with the program (Microsoft allows this).
set "UCRT="
for /d %%d in ("%ProgramFiles(x86)%\Windows Kits\10\Redist\10.*") do (
  if exist "%%d\ucrt\DLLs\x86\ucrtbase.dll" set "UCRT=%%d\ucrt\DLLs\x86"
)
if "%UCRT%"=="" if exist "%ProgramFiles(x86)%\Windows Kits\10\Redist\ucrt\DLLs\x86\ucrtbase.dll" (
  set "UCRT=%ProgramFiles(x86)%\Windows Kits\10\Redist\ucrt\DLLs\x86"
)
set "UCRT_ARG="
if not "%UCRT%"=="" (
  echo Including Windows 7 runtime files from: !UCRT!
  set UCRT_ARG=--add-binary "!UCRT!\*.dll;."
) else (
  echo NOTE: Windows SDK runtime files not found. Windows 7 PCs will need
  echo       update KB2999226 installed. Windows 8.1, 10 and 11 are not affected.
)

REM ---- 6. Program folder (used by the installer) ----------------------------
"%VPY%" -m PyInstaller --noconfirm --clean --windowed ^
  --name "%EXE%" ^
  --icon app\icon.ico ^
  --version-file build\version_info.txt ^
  --add-data "app\icon.png;." ^
  --paths app ^
  !UCRT_ARG! ^
  app\main.py || (echo PyInstaller build failed. & goto :fail)

REM ---- 7. Portable single-file .exe -----------------------------------------
"%VPY%" -m PyInstaller --noconfirm --onefile --windowed ^
  --name "%EXE%-Portable-%VER%" ^
  --icon app\icon.ico ^
  --version-file build\version_info.txt ^
  --add-data "app\icon.png;." ^
  --paths app ^
  !UCRT_ARG! ^
  --distpath build\portable ^
  --workpath build\portable-work ^
  app\main.py || (echo Portable build failed. & goto :fail)
copy /Y "build\portable\%EXE%-Portable-%VER%.exe" "%OUTDIR%\" >NUL

REM ---- 8. Setup.exe installer (Inno Setup) ----------------------------------
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
  echo   !OUTDIR!
  goto :fail
)
"%ISCC%" /Qp /DMyAppVersion=%VER% "/DOutputDir=%OUTDIR%" installer\windows_installer.iss || (echo Installer build failed. & goto :fail)

echo.
echo =====================================================================
echo  Done. Your Windows files are in:
echo    %OUTDIR%
echo    - %EXE%-Setup-%VER%.exe     (double-click to install)
echo    - %EXE%-Portable-%VER%.exe  (runs without installing)
echo  They run on Windows 7, 8, 8.1, 10 and 11 (32-bit and 64-bit).
echo =====================================================================
if "%CI%"=="" pause
exit /b 0

:fail
echo.
echo BUILD STOPPED - see the message above.
if "%CI%"=="" pause
exit /b 1

:find_iscc
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
exit /b 0
