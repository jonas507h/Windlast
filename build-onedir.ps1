$ErrorActionPreference = "Stop"

pyinstaller `
  --onedir `
  --windowed `
  --name "N&M Windlastrechner 2" `
  --icon "Logo\windlast.ico" `
  --paths . `
  --paths windlast_CORE `
  --add-data "windlast_UI;windlast_UI" `
  --add-data "windlast_CORE/materialdaten/*.csv;windlast_CORE/materialdaten" `
  --add-data "THIRD_PARTY_NOTICES.txt;." `
  windlast_API\app.py
