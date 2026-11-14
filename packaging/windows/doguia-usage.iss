; Instalador do doguia-usage para Windows (Inno Setup 6). Quem compila é packaging/build.py --installer, que passa
; AppVer, BinDir, OutDir e OutName. Instala só para o usuário, sem administrador, e põe a pasta no PATH do usuário.
#ifndef AppVer
  #define AppVer "0.0.0"
#endif
#ifndef BinDir
  #define BinDir "..\..\build\bin"
#endif
#ifndef OutDir
  #define OutDir "..\..\dist"
#endif
#ifndef OutName
  #define OutName "doguia-usage-setup"
#endif

[Setup]
AppId={{6F0C7B1E-5D2A-4C8B-9E1F-D0C1A1B2E3F4}
AppName=DoguIA Usage
AppVersion={#AppVer}
AppVerName=DoguIA Usage {#AppVer}
AppPublisher=DoguIA
AppPublisherURL=https://www.doguia.com.br
DefaultDirName={localappdata}\Programs\DoguIA Usage
DefaultGroupName=DoguIA Usage
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesEnvironment=yes
CloseApplications=force
OutputDir={#OutDir}
OutputBaseFilename={#OutName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\doguia-usage.exe
UninstallDisplayName=DoguIA Usage

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "{#BinDir}\doguia-usage.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BinDir}\doguia-usage-bg.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#DocDir}\INSTALACAO.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Configurar DoguIA Usage"; Filename: "{app}\doguia-usage.exe"; Parameters: "painel"
Name: "{group}\Diagnóstico do DoguIA Usage"; Filename: "{cmd}"; Parameters: "/k """"{app}\doguia-usage.exe"" doctor"""
Name: "{group}\Desinstalar DoguIA Usage"; Filename: "{uninstallexe}"

[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Check: NeedsAddPath(ExpandConstant('{app}'))

[Run]
; atualização com o envio já ligado: volta a enviar com a versão nova, sem depender do assistente
Filename: "{app}\doguia-usage-bg.exe"; Parameters: "run"; Flags: nowait runasoriginaluser; Check: AutostartOn
Filename: "{app}\doguia-usage.exe"; Parameters: "painel"; Description: "Abrir o assistente de configuração"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{app}\doguia-usage.exe"; Parameters: "uninstall"; Flags: runhidden waituntilterminated; RunOnceId: "DesligaInicio"
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM doguia-usage-bg.exe"; Flags: runhidden waituntilterminated; RunOnceId: "Encerra"

[Code]
const
  EnvKey = 'Environment';
  RunKey = 'Software\Microsoft\Windows\CurrentVersion\Run';

function NeedsAddPath(Dir: string): Boolean;
var
  Paths: string;
begin
  if not RegQueryStringValue(HKCU, EnvKey, 'Path', Paths) then
    Result := True
  else
    Result := Pos(';' + Uppercase(Dir) + ';', ';' + Uppercase(Paths) + ';') = 0;
end;

procedure RemovePath(Dir: string);
var
  Paths: string;
  P: Integer;
begin
  if not RegQueryStringValue(HKCU, EnvKey, 'Path', Paths) then
    exit;
  Paths := ';' + Paths + ';';
  P := Pos(';' + Uppercase(Dir) + ';', Uppercase(Paths));
  if P = 0 then
    exit;
  Delete(Paths, P, Length(Dir) + 1);
  RegWriteExpandStringValue(HKCU, EnvKey, 'Path', Copy(Paths, 2, Length(Paths) - 2));
end;

function AutostartOn: Boolean;
begin
  Result := RegValueExists(HKCU, RunKey, 'DoguIAUsage');
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Code: Integer;
begin
  { o envio em segundo plano prende o .exe: sem isto a atualização não consegue substituí-lo }
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM doguia-usage-bg.exe', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Result := '';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RemovePath(ExpandConstant('{app}'));
end;
