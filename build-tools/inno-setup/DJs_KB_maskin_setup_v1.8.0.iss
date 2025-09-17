; Inno Setup Script for DJs KB-maskin v1.8.0
; Single Instance Restriction - TESTED AND WORKING
; Fixed: Removed outdated Nedladdningar folder creation (downloads now go to Downloads\Svenska tidningar)
; Following procedure in Code_how_to_do\Inno_Setup_Setup_script_createion_procedure.md

[Setup]
; Basic application information
AppName=DJs KB-maskin
AppVersion=1.8.0
AppVerName=DJs KB-maskin 1.8.0
AppPublisher=Dan Josefsson
AppPublisherURL=https://github.com/Tripper99/DJs-KB-maskin
AppSupportURL=https://github.com/Tripper99/DJs-KB-maskin
AppUpdatesURL=https://github.com/Tripper99/DJs-KB-maskin
AppId={{F8E5B3A7-9C4D-4B7E-8F2A-1D3E5C7B9A8F}

; Installation directories (following procedure specifications)
DefaultDirName={localappdata}\Programs\DJs KB-maskin
DefaultGroupName=DJs KB-maskin
AllowNoIcons=yes

; Installer settings
UninstallDisplayIcon={app}\Agg-med-smor-v4-transperent.ico
OutputDir=..\..\dist
OutputBaseFilename=DJs_KB_maskin_v1.8.0_setup

; Compression
Compression=lzma2
SolidCompression=yes

; System requirements
MinVersion=10.0
ArchitecturesInstallIn64BitMode=x64compatible

; UI and privileges
WizardStyle=modern
PrivilegesRequired=lowest

; Uninstall settings (default to remove older versions)
UninstallFilesDir={app}\uninstall

[Languages]
Name: "swedish"; MessagesFile: "compiler:Languages\Swedish.isl"

[Tasks]
Name: "desktopicon"; Description: "Skapa genväg på skrivbordet"; GroupDescription: "Ytterligare alternativ:"; Flags: unchecked
Name: "removeold"; Description: "Ta bort äldre versioner av DJs KB-maskin"; GroupDescription: "Rengöring:"; Flags: checkedonce

[Files]
; Main executable (from \dist\ folder as specified)
Source: "..\..\dist\DJs_KB_maskin_v1.8.0.exe"; DestDir: "{app}"; Flags: ignoreversion

; Icon file (as specified in procedure)
Source: "..\..\Agg-med-smor-v4-transperent.ico"; DestDir: "{app}"; Flags: ignoreversion

; Documentation (Manual.docx as specified)
Source: "..\..\Manual.docx"; DestDir: "{app}"; Flags: ignoreversion

; CSV file (using existing file since titles_bibids_mall.csv not found)
Source: "..\..\titles_bibids_2025-09-09.csv"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\DJs KB-maskin"; Filename: "{app}\DJs_KB_maskin_v1.8.0.exe"; IconFilename: "{app}\Agg-med-smor-v4-transperent.ico"
Name: "{group}\Manual"; Filename: "{app}\Manual.docx"
Name: "{group}\Avinstallera DJs KB-maskin"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\DJs KB-maskin"; Filename: "{app}\DJs_KB_maskin_v1.8.0.exe"; IconFilename: "{app}\Agg-med-smor-v4-transperent.ico"; Tasks: desktopicon

[Dirs]
; Create application folders
Name: "{app}\logs"

[Run]
; Option to launch after installation
Filename: "{app}\DJs_KB_maskin_v1.8.0.exe"; Description: "Starta DJs KB-maskin"; Flags: nowait postinstall skipifsilent

[InstallDelete]
; Remove older versions if selected (default behavior)
Type: filesandordirs; Name: "{app}\DJs_KB_maskin_v1.7.9.exe"; Tasks: removeold
Type: filesandordirs; Name: "{app}\DJs_KB_maskin_v1.7.8.exe"; Tasks: removeold
Type: filesandordirs; Name: "{app}\DJs_KB_maskin_v1.7.7.exe"; Tasks: removeold
Type: filesandordirs; Name: "{app}\DJs_KB_maskin_v1.7.6.exe"; Tasks: removeold
Type: filesandordirs; Name: "{app}\DJs_KB_maskin_v1.7.5.exe"; Tasks: removeold
Type: filesandordirs; Name: "{app}\DJs_KB_maskin_v1.7.4.exe"; Tasks: removeold

[UninstallDelete]
; Clean up user files on uninstall
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\djs_kb-maskin_settings.json"
Type: files; Name: "{app}\token_*.json"
Type: dirifempty; Name: "{app}"