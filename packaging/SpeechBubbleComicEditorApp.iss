#ifndef MyAppVersion
  #define MyAppVersion "0.1.8"
#endif
#ifndef MyAppWindowsVersion
  #define MyAppWindowsVersion "0.1.8.0"
#endif
#ifndef MySourceDir
  #define MySourceDir "..\dist\SpeechBubbleComicEditorApp"
#endif

#define MyAppName "Speech Bubble Comic Editor App"
#define MyAppExeName "SpeechBubbleComicEditorApp.exe"

[Setup]
AppId={{37342494-2D3C-47DD-85FE-6C683D98D37D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
VersionInfoVersion={#MyAppWindowsVersion}
VersionInfoProductVersion={#MyAppWindowsVersion}
AppPublisher=ukr8b3g-cmyk
AppPublisherURL=https://github.com/ukr8b3g-cmyk/Speech-Bubble-Comic-Editor-App
AppSupportURL=https://github.com/ukr8b3g-cmyk/Speech-Bubble-Comic-Editor-App/issues
DefaultDirName={localappdata}\Programs\Speech Bubble Comic Editor App
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\release
OutputBaseFilename=SpeechBubbleComicEditorApp-v{#MyAppVersion}-win-x64-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\web\assets\speech-bubble-comic-editor-app.ico
SetupLogging=yes

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
