; Inno Setup Script for DJs KB-maskin v1.7.5

#define MyAppName "DJs KB-maskin"
#define MyAppVersion "1.7.5"
#define MyAppPublisher "Dan Josefsson"
#define MyAppURL "https://github.com/Tripper99/DJs-KB-maskin"
#define MyAppExeName "DJs_KB_maskin_v1.7.5.exe"

[Setup]
AppId={{F8E5B3A7-9C4D-4B7E-8F2A-1D3E5C7B9A8F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=yes
OutputDir=C:\Dropbox\Dokument\Programmering\Python\App DJs KB-maskin\DJs_KB_maskin (project)\build-tools\output\installer
OutputBaseFilename=DJs_KB_maskin_v{#MyAppVersion}_setup
Compression=lzma2/max
SolidCompression=yes
MinVersion=10.0
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ShowLanguageDialog=no

[Languages]
Name: "swedish"; MessagesFile: "compiler:Languages\Swedish.isl"

[CustomMessages]
swedish.LaunchProgram=Starta {#MyAppName}
swedish.CreateDesktopIcon=Skapa genväg på skrivbordet

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "Ytterligare uppgifter:"; Flags: unchecked

[Files]
Source: "C:\Dropbox\Dokument\Programmering\Python\App DJs KB-maskin\DJs_KB_maskin (project)\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Dropbox\Dokument\Programmering\Python\App DJs KB-maskin\DJs_KB_maskin (project)\Manual.docx"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Dropbox\Dokument\Programmering\Python\App DJs KB-maskin\DJs_KB_maskin (project)\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Dropbox\Dokument\Programmering\Python\App DJs KB-maskin\DJs_KB_maskin (project)\titles_bibids_2025-09-09.csv"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Dropbox\Dokument\Programmering\Python\App DJs KB-maskin\DJs_KB_maskin (project)\Agg-med-smor-v4-transperent.ico"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\Nedladdningar"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Manual"; Filename: "{app}\Manual.docx"
Name: "{group}\CSV-mall"; Filename: "{app}\titles_bibids_2025-09-09.csv"
Name: "{group}\README"; Filename: "{app}\README.md"
Name: "{group}\Avinstallera {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\djs_kb-maskin_settings.json"
Type: files; Name: "{app}\token_*.json"
Type: dirifempty; Name: "{app}\Nedladdningar"
Type: dirifempty; Name: "{app}"

[Code]
procedure CurPageChanged(CurPageID: Integer);
begin
  case CurPageID of
    wpWelcome:
      WizardForm.WelcomeLabel2.Caption := 
        'Den här guiden kommer att installera {#MyAppName} version {#MyAppVersion} på din dator.' + #13#10 + #13#10 +
        'DJs KB-maskin är ett verktyg för att hantera tidningsfiler från "Svenska Tidningar". ' +
        'Version 1.7.5 innehåller en kritisk buggfix för standardmappar.' + #13#10 + #13#10 +
        'Klicka på Nästa för att fortsätta.';
    
    wpSelectDir:
      WizardForm.SelectDirLabel.Caption := 
        'Var vill du installera {#MyAppName}?' + #13#10 + #13#10 +
        'Välj installationsmapp nedan. Klicka på Bläddra för att välja en annan mapp.';
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    if MsgBox('Installation slutförd!' + #13#10 + #13#10 + 
              'Version 1.7.5 fixar problemet där filer försvann när standardmappen användes.' + #13#10 + #13#10 +
              'Vill du öppna manualen nu?', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      ShellExec('open', ExpandConstant('{app}\Manual.docx'), '', '', SW_SHOW, ewNoWait, ResultCode);
    end;
  end;
end;