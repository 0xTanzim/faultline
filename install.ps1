# Faultline Universal Installer Wrapper (PowerShell)
# Supports both local repository execution and remote streamed one-liner execution:
#   irm https://raw.githubusercontent.com/0xTanzim/faultline/main/install.ps1 | iex
$ErrorActionPreference = "Stop"

$ScriptDir = ""
if ($MyInvocation.MyCommand.Path) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

if ($ScriptDir -and (Test-Path "$ScriptDir\install.py")) {
    & python "$ScriptDir\install.py" @args
    exit $LASTEXITCODE
}

# Streamed remote execution
$TempDir = Join-Path $env:TEMP ("faultline-" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

try {
    $ZipPath = Join-Path $TempDir "faultline.zip"
    $RepoZip = "https://github.com/0xTanzim/faultline/archive/refs/heads/main.zip"
    Write-Host "Fetching latest Faultline release from GitHub..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $RepoZip -OutFile $ZipPath
    Expand-Archive -Path $ZipPath -DestinationPath $TempDir -Force

    $ExtractedRoot = Join-Path $TempDir "faultline-main"
    if ($args.Count -eq 0) {
        & python "$ExtractedRoot\install.py" "."
    } else {
        & python "$ExtractedRoot\install.py" @args
    }
    exit $LASTEXITCODE
} finally {
    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
}
