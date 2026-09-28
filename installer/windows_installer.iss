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
  #define MyAppVersion "1.1.0"
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
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
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

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Visit www.techmiary.tech"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
