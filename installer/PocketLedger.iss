; Inno Setup script for Pocket Ledger v{{VERSION}}.
; User data is NOT installed here and is never removed by the uninstaller.
; Installed data path: %LOCALAPPDATA%\Pocket Ledger\data

#ifndef AppVersion
  #define AppVersion "0.4.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\build\windows-release\pyinstaller-dist\PocketLedger"
#endif
#ifndef OutputDir
  #define OutputDir "..\build\windows-release\artifacts"
#endif

#define AppName "Pocket Ledger"
#define AppId "{{ED392460-6489-4DF1-88F0-E4D0E9141091}}"
#define ExeName "PocketLedger.exe"
#define AppVersionFull AppVersion + ".0"

[Setup]
AppId={{ED392460-6489-4DF1-88F0-E4D0E9141091}}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
VersionInfoVersion={#AppVersionFull}
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersionFull}
AppPublisher=Pocket Ledger
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
DisableDirPage=no
DisableProgramGroupPage=no
AllowNoIcons=yes
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
OutputBaseFilename=PocketLedger-v{#AppVersion}-win64-setup
SetupIconFile=..\icons\PC.ico
UninstallDisplayIcon={app}\{#ExeName}
UninstallDisplayName={#AppName} v{#AppVersion}
; No UninstallDelete entries: %LOCALAPPDATA%\Pocket Ledger\data is user data.

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExeName}"; IconFilename: "{app}\{#ExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
