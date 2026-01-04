$ErrorActionPreference = "Stop"

# 1) Onedir-Build
.\build-onedir.ps1

# 2) Installer bauen
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
