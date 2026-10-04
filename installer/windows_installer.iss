; ---------------------------------------------------------------------------
; Inno Setup script - builds the Windows "Setup.exe" installer for
; Techmiary School Result Manager.
;
; You normally do NOT run this by hand: build_windows.bat does it for you and
; passes the version number from app\branding.py.
;
; IMPORTANT: keep AppId the same forever. That is how Windows knows a new
; Setup.exe is an UPGRADE of the installed program (it replaces the old files
; and keeps the school's data, which lives in %APPDATA%).
; ---------------------------------------------------------------------------

#ifndef MyAppVersion
  #define MyAppVersion "1.2.0"
#endif
#ifndef OutputDir
  #define OutputDir "..\..\Installers\Windows"
#endif

#define MyAppName      "Techmiary School Result Manager"
#define MyAppPublisher "Techmiary Technology Concept"
#define MyAppURL       "https://www.techmiary.tech"
#define MyAppExeName   "TechmiarySchoolResultManager.exe"

[Setup]
AppId={{C5152723-6CA0-4685-A65D-CA592D0CC29B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=(c) {#MyAppPublisher} - www.techmiary.tech
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
DefaultDirName={autopf}\Techmiary\School Result Manager
DefaultGroupName=Techmiary School Result Manager
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=TechmiarySchoolResultManager-Setup-{#MyAppVersion}
SetupIconFile=..\app\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; 32-bit program: installs on both 32-bit and 64-bit Windows.
; Windows 7 SP1 is the oldest supported version (7, 8, 8.1, 10, 11).
MinVersion=6.1sp1
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Everything PyInstaller produced in dist\TechmiarySchoolResultManager\
Source: "..\dist\TechmiarySchoolResultManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; Remove old program files before an upgrade (school data is NOT here, it is safe)
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\PySide2"
Type: filesandordirs; Name: "{app}\PySide6"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Visit www.techmiary.tech"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Version 1.1.0 was a 64-bit program. This 32-bit installer cannot see it in the
// normal place, so we look for it and remove it quietly first (school data,
// kept in %APPDATA%, is NOT touched). This avoids two copies in "Installed apps".
const
  OldKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{C5152723-6CA0-4685-A65D-CA592D0CC29B}_is1';

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Uninstaller: String;
  ResultCode: Integer;
begin
  Result := '';
  if IsWin64 and RegQueryStringValue(HKLM64, OldKey, 'UninstallString', Uninstaller) then
  begin
    Uninstaller := RemoveQuotes(Uninstaller);
    if FileExists(Uninstaller) then
      Exec(Uninstaller, '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART', '',
           SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
