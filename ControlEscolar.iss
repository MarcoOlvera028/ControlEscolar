[Setup]
AppName=Control Escolar
AppVersion=1.0
DefaultDirName={localappdata}\Control Escolar
DefaultGroupName=Control Escolar
OutputDir=installer
OutputBaseFilename=Setup_Control_Escolar
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\Control Escolar\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Control Escolar"; Filename: "{app}\Control Escolar.exe"
Name: "{commondesktop}\Control Escolar"; Filename: "{app}\Control Escolar.exe"

[Run]
Filename: "{app}\Control Escolar.exe"; Description: "Ejecutar Control Escolar"; Flags: nowait postinstall skipifsilent
