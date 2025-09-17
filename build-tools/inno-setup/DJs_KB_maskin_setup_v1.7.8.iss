; Inno Setup Script for DJs KB-maskin v1.7.8
; Using simplified, proven syntax based on official documentation

[Setup]
; Basic application information
AppName=DJs KB-maskin
AppVersion=1.7.8
AppVerName=DJs KB-maskin 1.7.8
AppPublisher=Dan Josefsson
AppPublisherURL=https://github.com/Tripper99/DJs-KB-maskin
AppSupportURL=https://github.com/Tripper99/DJs-KB-maskin
AppUpdatesURL=https://github.com/Tripper99/DJs-KB-maskin
AppId={{F8E5B3A7-9C4D-4B7E-8F2A-1D3E5C7B9A8F}

; Installation directories
DefaultDirName={autopf}\DJs KB-maskin
DefaultGroupName=DJs KB-maskin

; Installer settings
; SetupIconFile removed due to Windows resource update error
UninstallDisplayIcon={app}\Agg-med-smor-v4-transperent.ico
OutputDir=..\..\dist
OutputBaseFilename=DJs_KB_maskin_v1.7.8_setup

; Compression
Compression=lzma2
SolidCompression=yes

; System requirements
MinVersion=10.0
ArchitecturesInstallIn64BitMode=x64compatible

; UI
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "swedish"; MessagesFile: "compiler:Languages\Swedish.isl"

[Tasks]
Name: "desktopicon"; Description: "Skapa genväg på skrivbordet"; GroupDescription: "Ytterligare alternativ:"; Flags: unchecked

[Files]
; Main executable
Source: "..\..\dist\DJs_KB_maskin_v1.7.8.exe"; DestDir: "{app}"; Flags: ignoreversion

; Icon file
Source: "..\..\Agg-med-smor-v4-transperent.ico"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "..\..\Manual.docx"; DestDir: "{app}"; Flags: ignoreversion

; CSV file
Source: "..\..\titles_bibids_2025-09-09.csv"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\DJs KB-maskin"; Filename: "{app}\DJs_KB_maskin_v1.7.8.exe"; IconFilename: "{app}\Agg-med-smor-v4-transperent.ico"
Name: "{group}\Manual"; Filename: "{app}\Manual.docx"
Name: "{group}\Avinstallera DJs KB-maskin"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\DJs KB-maskin"; Filename: "{app}\DJs_KB_maskin_v1.7.8.exe"; IconFilename: "{app}\Agg-med-smor-v4-transperent.ico"; Tasks: desktopicon

[Dirs]
; Create application folders
Name: "{app}\logs"

[Run]
; Option to launch after installation
Filename: "{app}\DJs_KB_maskin_v1.7.8.exe"; Description: "Starta DJs KB-maskin"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up user files on uninstall
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\djs_kb-maskin_settings.json"
Type: files; Name: "{app}\token_*.json"
Type: dirifempty; Name: "{app}"