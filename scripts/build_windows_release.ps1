<#
.SYNOPSIS
Builds reproducible Windows release artifacts for Pocket Ledger.

.OUTPUTS
build/windows-release/artifacts/PocketLedger-vX.Y.Z-win64-portable.zip
build/windows-release/artifacts/PocketLedger-vX.Y.Z-win64-setup.exe
build/windows-release/artifacts/SHA256SUMS.txt
build/windows-release/artifacts/RELEASE_NOTES.md
#>

[CmdletBinding()]
param(
    [string] $Version,
    [switch] $SkipInstaller
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    throw "Virtual environment not found at $python. Create it and install requirements.txt first."
}

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = (& $python -c "from version import APP_VERSION; print(APP_VERSION)").Trim()
}
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Version must be semantic X.Y.Z; got '$Version'."
}

& $python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is missing. Run: .\.venv\Scripts\python.exe -m pip install -r requirements-build.txt"
}

function Find-ISCC {
    $candidates = @()
    if ($env:LOCALAPPDATA) {
        $candidates += Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
    }
    $candidates += 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
    $candidates += 'C:\Program Files\Inno Setup 6\ISCC.exe'
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    throw 'Inno Setup 6 was not found. Install it (winget install JRSoftware.InnoSetup) or add ISCC.exe to PATH.'
}

$buildRoot = Join-Path $root 'build\windows-release'
$artifactDir = Join-Path $buildRoot 'artifacts'
$pyinstallerDist = Join-Path $buildRoot 'pyinstaller-dist'
$pyinstallerWork = Join-Path $buildRoot 'pyinstaller-work'
$stageRoot = Join-Path $buildRoot 'stage'

if (Test-Path $buildRoot) {
    Remove-Item -Path $buildRoot -Recurse -Force
}
foreach ($dir in @($artifactDir, $pyinstallerDist, $pyinstallerWork, $stageRoot)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

Write-Host "Building PyInstaller bundle for v$Version..."
& $python -m PyInstaller --clean --noconfirm `
    --distpath $pyinstallerDist `
    --workpath $pyinstallerWork `
    (Join-Path $root 'PocketLedger.spec')
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }

$sourceDir = Join-Path $pyinstallerDist 'PocketLedger'
if (-not (Test-Path (Join-Path $sourceDir 'PocketLedger.exe'))) {
    throw "Expected EXE was not produced in $sourceDir"
}

$portableName = "PocketLedger-v$Version-win64-portable"
$portableStage = Join-Path $stageRoot $portableName
New-Item -ItemType Directory -Path $portableStage -Force | Out-Null
Copy-Item -Path (Join-Path $sourceDir '*') -Destination $portableStage -Recurse -Force
Set-Content -Path (Join-Path $portableStage 'portable.marker') -Value 'portable' -Encoding ascii
$portableNote = @"
Pocket Ledger $Version - portable Windows build

Extract this folder anywhere and run PocketLedger.exe. No installation or
administrator rights are required. Your database is created in this folder's
data\ directory; keep the whole folder when moving or backing up the app.
"@
Set-Content -Path (Join-Path $portableStage 'PORTABLE.txt') -Value $portableNote -Encoding utf8

$zipPath = Join-Path $artifactDir "$portableName.zip"
Compress-Archive -Path (Join-Path $portableStage '*') -DestinationPath $zipPath -Force
Write-Host "Portable ZIP: $zipPath"

$setupPath = Join-Path $artifactDir "PocketLedger-v$Version-win64-setup.exe"
if ($SkipInstaller) {
    Write-Host 'SkipInstaller requested: setup EXE was not built.'
} else {
    $iscc = Find-ISCC
    $iss = Join-Path $root 'installer\PocketLedger.iss'
    Write-Host "Building installer with $iscc..."
    & $iscc "/dAppVersion=$Version" "/dSourceDir=$sourceDir" "/dOutputDir=$artifactDir" $iss
    if ($LASTEXITCODE -ne 0) { throw 'Inno Setup build failed.' }
    if (-not (Test-Path $setupPath)) { throw "Expected installer was not produced at $setupPath" }
    Write-Host "Installer EXE: $setupPath"
}

$artifacts = @($zipPath)
if (-not $SkipInstaller) { $artifacts += $setupPath }
$checksumLines = foreach ($artifact in $artifacts) {
    if (-not (Test-Path $artifact)) { throw "Missing artifact: $artifact" }
    $hash = (Get-FileHash -Algorithm SHA256 -Path $artifact).Hash.ToLowerInvariant()
    '{0}  {1}' -f $hash, [System.IO.Path]::GetFileName($artifact)
}
$checksumPath = Join-Path $artifactDir 'SHA256SUMS.txt'
[System.IO.File]::WriteAllLines(
    $checksumPath,
    $checksumLines,
    (New-Object System.Text.UTF8Encoding($false))
)

$templatePath = Join-Path $root 'docs\release_notes_template.md'
$notes = Get-Content -Path $templatePath -Raw
$notes = $notes.Replace('{{VERSION}}', $Version)
$notesPath = Join-Path $artifactDir 'RELEASE_NOTES.md'
[System.IO.File]::WriteAllText(
    $notesPath,
    $notes,
    (New-Object System.Text.UTF8Encoding($false))
)

Write-Host "Checksums: $checksumPath"
Write-Host "Release notes: $notesPath"
Write-Host 'Windows release build complete.'
