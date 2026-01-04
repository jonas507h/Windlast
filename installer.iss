[Setup]
AppName=N&M Windlastrechner 2
AppVersion=2.0
DefaultDirName={pf}\N&M Windlastrechner 2
DefaultGroupName=N&M Windlastrechner 2
OutputDir=dist
OutputBaseFilename=N&M_Windlastrechner_2_Setup
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes

[Files]
Source: "dist\N&M Windlastrechner 2\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\N&M Windlastrechner 2"; Filename: "{app}\N&M Windlastrechner 2.exe"
Name: "{commondesktop}\N&M Windlastrechner 2"; Filename: "{app}\N&M Windlastrechner 2.exe"

[Run]
Filename: "{app}\N&M Windlastrechner 2.exe"; Description: "N&M Windlastrechner 2 starten"; Flags: nowait postinstall skipifsilent
