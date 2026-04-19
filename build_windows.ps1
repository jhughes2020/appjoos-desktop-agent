param(
    [switch]$OneFile
)

$AppName        = "Systems Agent"
$ExeName        = "SystemsAgent"
$CompanyName    = "AppJoos"
$AuthorName     = "J.Hughes"
$ProductVersion = "0.1.0"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "Project root: $ProjectRoot"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Creating Windows virtual environment..."
    python -m venv .venv
}

$Py = ".\.venv\Scripts\python.exe"

Write-Host "Installing dependencies..."
& $Py -m pip install --upgrade pip
& $Py -m pip install -r requirements.txt
& $Py -m pip install pyinstaller

$VersionFile = Join-Path $ProjectRoot "version_info.txt"
@"
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(0,1,0,0),
    prodvers=(0,1,0,0),
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
          StringStruct("CompanyName", "$CompanyName"),
          StringStruct("FileDescription", "$AppName"),
          StringStruct("FileVersion", "$ProductVersion"),
          StringStruct("InternalName", "$ExeName"),
          StringStruct("LegalCopyright", "Copyright (c) $AuthorName"),
          StringStruct("OriginalFilename", "$ExeName.exe"),
          StringStruct("ProductName", "$AppName"),
          StringStruct("ProductVersion", "$ProductVersion")
        ]
      )
    ]),
    VarFileInfo([VarStruct("Translation", [1033, 1200])])
  ]
)
"@ | Set-Content -Path $VersionFile -Encoding UTF8

$IconPath = Join-Path $ProjectRoot "app_icon.ico"

if (-not (Test-Path $IconPath)) {
    Write-Host "No app_icon.ico found in project root."
    Write-Host "Build will continue without a custom icon."
}

Write-Host "Cleaning old build output..."
Remove-Item .\build -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item .\dist -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item ".\$ExeName.spec" -Force -ErrorAction SilentlyContinue

$PyInstallerArgs = @(
    "-m", "PyInstaller",
    "--name", $ExeName,
    "--windowed",
    "--version-file", $VersionFile
)

if (Test-Path $IconPath) {
    $PyInstallerArgs += @("--icon", $IconPath)
}

if ($OneFile) {
    $PyInstallerArgs += "--onefile"
}

$PyInstallerArgs += "main.py"

Write-Host "Running PyInstaller..."
& $Py @PyInstallerArgs

Write-Host ""
Write-Host "Build complete."
if ($OneFile) {
    Write-Host "Output: .\dist\$ExeName.exe"
} else {
    Write-Host "Output: .\dist\$ExeName\"
}
