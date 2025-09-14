; Inno Setup Script for DJs KB-maskin
; Created: 2025-09-14
; Version: 1.7.7

#define MyAppName "DJs KB-maskin"
#define MyAppVersion "1.7.7"
#define MyAppPublisher "Dan Josefsson"
#define MyAppURL "https://github.com/Tripper99/DJs-KB-maskin"
#define MyAppExeName "DJs_KB_maskin_v1.7.7.exe"
#define MyAppCopyright "Copyright (C) 2025 Dan Josefsson"

; Define paths relative to the project root
#define ProjectRoot "..\..\"
#define BuildOutputExe ProjectRoot + "dist\"
#define ResourcesDir ProjectRoot + "build-tools\resources\"

[Setup]
; Basic application information
AppId={{F8E5B3A7-9C4D-4B7E-8F2A-1D3E5C7B9A8F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright={#MyAppCopyright}

; Directory settings
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=DJs_KB_maskin_v{#MyAppVersion}_setup
VersionInfoVersion={#MyAppVersion}

; Compression settings
Compression=lzma2/max
SolidCompression=yes
CompressionThreads=auto

; Windows version requirements
MinVersion=10.0
ArchitecturesInstallIn64BitMode=x64compatible

; UI settings
WizardStyle=modern
UninstallDisplayIcon={app}\Agg-med-smor-v4-transperent.ico
UninstallDisplayName={#MyAppName}

; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Language settings (Swedish)
ShowLanguageDialog=no

[Languages]
Name: "swedish"; MessagesFile: "compiler:Languages\Swedish.isl"

[CustomMessages]
swedish.LaunchProgram=Starta {#MyAppName}
swedish.CreateDesktopIcon=Skapa genväg på skrivbordet
swedish.AdditionalTasks=Ytterligare uppgifter:

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalTasks}"; Flags: unchecked

[Files]
; Main executable
Source: "{#BuildOutputExe}{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Icon file (for application use)
Source: "{#ProjectRoot}Agg-med-smor-v4-transperent.ico"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "{#ProjectRoot}Manual.docx"; DestDir: "{app}"; Flags: ignoreversion

; CSV template - using the current CSV file as template
Source: "{#ProjectRoot}titles_bibids_2025-09-09.csv"; DestDir: "{app}"; DestName: "titles_bibids_mall.csv"; Flags: ignoreversion

; Create default folders
[Dirs]
Name: "{app}\logs"; Permissions: users-modify

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\Agg-med-smor-v4-transperent.ico"
Name: "{group}\Manual"; Filename: "{app}\Manual.docx"
Name: "{group}\CSV Mall för Tidningskoder"; Filename: "{app}\titles_bibids_mall.csv"
Name: "{group}\Avinstallera {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\Agg-med-smor-v4-transperent.ico"; Tasks: desktopicon

[Run]
; Option to launch the application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up configuration and log files on uninstall
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\djs_kb-maskin_settings.json"
Type: files; Name: "{app}\token_*.json"
Type: dirifempty; Name: "{app}"

[Code]
// Check if .NET Framework or Visual C++ redistributables are needed
function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // Add any prerequisite checks here if needed
  // For example, checking for Python runtime or specific Windows features
end;

// Custom messages in Swedish
procedure CurPageChanged(CurPageID: Integer);
begin
  case CurPageID of
    wpWelcome:
      WizardForm.WelcomeLabel2.Caption := 
        'Den här guiden kommer att installera {#MyAppName} version {#MyAppVersion} på din dator.' + #13#10 + #13#10 +
        'DJs KB-maskin är ett verktyg för att hantera tidningsfiler från "Svenska Tidningar". ' +
        'Programmet kan ladda ner JPG-bilagor från Gmail och konvertera dem till PDF-filer med korrekta namn för KB.' + #13#10 + #13#10 +
        'Version {#MyAppVersion} Nyheter:' + #13#10 +
        '• Automatisk återställning av inställningar vid versionsuppdatering' + #13#10 +
        '• Säkerställer att nya standardvärden används efter uppgradering' + #13#10 +
        '• Nedladdningar går till "Svenska tidningar" i din Nedladdningar-mapp' + #13#10 +
        '• Förbättrad mappvalidering och felhantering' + #13#10 + #13#10 +
        'Klicka på Nästa för att fortsätta.';
    
    wpSelectDir:
      WizardForm.SelectDirLabel.Caption := 
        'Var vill du installera {#MyAppName}?' + #13#10 + #13#10 +
        'Installationsprogrammet kommer att installera {#MyAppName} i följande mapp. ' +
        'För att installera i en annan mapp, klicka på Bläddra och välj en annan mapp.';
        
    wpReady:
      WizardForm.ReadyLabel.Caption := 
        'Installationsprogrammet är nu redo att installera {#MyAppName} på din dator.' + #13#10 + #13#10 +
        'Klicka på Installera för att fortsätta med installationen, eller klicka på Bakåt om du vill granska eller ändra några inställningar.';
  end;
end;

// Show release notes after successful installation
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Optionally open the manual after installation
    if MsgBox('Installation slutförd!' + #13#10 + #13#10 + 
              'Version {#MyAppVersion} är nu installerad.' + #13#10 + #13#10 +
              'VIKTIGT: Gamla inställningar har automatiskt återställts för att' + #13#10 +
              'säkerställa kompatibilitet med nya funktioner.' + #13#10 + #13#10 +
              'Standardmappen för nedladdningar är nu:' + #13#10 +
              '"Svenska tidningar" i din Nedladdningar-mapp.' + #13#10 + #13#10 +
              'Vill du öppna manualen nu?', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      ShellExec('open', ExpandConstant('{app}\Manual.docx'), '', '', SW_SHOW, ewNoWait, ResultCode);
    end;
  end;
end;