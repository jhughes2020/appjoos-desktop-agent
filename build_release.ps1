param(
    [switch]$OneFile
)

Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    python -m venv .venv
}

$Py = ".\.venv\Scripts\python.exe"

& $Py -m pip install --upgrade pip
& $Py -m pip install -r requirements.txt
& $Py -m pip install pyinstaller

$MetaHelper = Join-Path $PSScriptRoot "_build_meta.py"

@'
import json
import re
from desktop_agent.config.app_version import (
    APP_NAME,
    APP_VERSION,
    APP_DISPLAY_NAME,
    COMPANY_NAME,
    AUTHOR_NAME,
)

parts = []
for p in APP_VERSION.split("."):
    try:
        parts.append(int(p))
    except ValueError:
        parts.append(0)

parts = (parts + [0, 0, 0, 0])[:4]
exe_name = re.sub(r"[^A-Za-z0-9]", "", APP_NAME) or "DesktopAgent"

print(json.dumps({
    "APP_NAME": APP_NAME,
    "APP_VERSION": APP_VERSION,
    "APP_DISPLAY_NAME": APP_DISPLAY_NAME,
    "COMPANY_NAME": COMPANY_NAME,
    "AUTHOR_NAME": AUTHOR_NAME,
    "EXE_NAME": exe_name,
    "VERSION_0": parts[0],
    "VERSION_1": parts[1],
    "VERSION_2": parts[2],
    "VERSION_3": parts[3],
}))
'@ | Set-Content -Path $MetaHelper -Encoding UTF8

$metaJson = & $Py $MetaHelper
$metaExit = $LASTEXITCODE
Remove-Item $MetaHelper -Force -ErrorAction SilentlyContinue

if ($metaExit -ne 0 -or [string]::IsNullOrWhiteSpace($metaJson)) {
    throw "Failed to generate build metadata from app_version.py"
}

$meta = $metaJson | ConvertFrom-Json

$VersionFile = Join-Path $PSScriptRoot "version_info.txt"

@"
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=($($meta.VERSION_0), $($meta.VERSION_1), $($meta.VERSION_2), $($meta.VERSION_3)),
    prodvers=($($meta.VERSION_0), $($meta.VERSION_1), $($meta.VERSION_2), $($meta.VERSION_3)),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        "040904B0",
        [
          StringStruct("CompanyName", "$($meta.COMPANY_NAME)"),
          StringStruct("FileDescription", "$($meta.APP_DISPLAY_NAME)"),
          StringStruct("FileVersion", "$($meta.APP_VERSION)"),
          StringStruct("InternalName", "$($meta.EXE_NAME)"),
          StringStruct("LegalCopyright", "Copyright (c) $($meta.AUTHOR_NAME)"),
          StringStruct("OriginalFilename", "$($meta.EXE_NAME).exe"),
          StringStruct("ProductName", "$($meta.APP_DISPLAY_NAME)"),
          StringStruct("ProductVersion", "$($meta.APP_VERSION)")
        ]
      )
    ]),
    VarFileInfo([VarStruct("Translation", [1033, 1200])])
  ]
)
"@ | Set-Content -Path $VersionFile -Encoding UTF8

Remove-Item .\build -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item .\dist -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item ".\$($meta.EXE_NAME).spec" -Force -ErrorAction SilentlyContinue

$PyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--name", $meta.EXE_NAME,
    "--windowed",
    "--version-file", $VersionFile
)

if (Test-Path ".\app_icon.ico") {
    $PyInstallerArgs += @("--icon", ".\app_icon.ico")
}

if ($OneFile) {
    $PyInstallerArgs += "--onefile"
}

$PyInstallerArgs += "main.py"

Write-Host ""
Write-Host "Building $($meta.APP_DISPLAY_NAME)..."
& $Py @PyInstallerArgs

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

Write-Host ""
Write-Host "Build complete."

if ($OneFile) {
    Write-Host "Output: .\dist\$($meta.EXE_NAME).exe"
} else {
    Write-Host "Output: .\dist\$($meta.EXE_NAME)\$($meta.EXE_NAME).exe"
}