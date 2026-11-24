<#
.SYNOPSIS
Verifies the built Pocket Ledger Windows release artifacts.

Checks checksums, portable startup in a clean folder, clean install, upgrade,
Apps & Features registration, uninstall, and user-data preservation.
#>

[CmdletBinding()]
param(
    [string] $ArtifactDir,
    [string] $WorkDir
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($ArtifactDir)) {
    $ArtifactDir = Join-Path $root 'build\windows-release\artifacts'
}
if ([string]::IsNullOrWhiteSpace($WorkDir)) {
    $WorkDir = Join-Path $root 'build\windows-release\verification'
}

$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw "Python not found at $python" }

if (Test-Path $WorkDir) { Remove-Item -Path $WorkDir -Recurse -Force }
New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null

$version = (& $python -c "from version import APP_VERSION; print(APP_VERSION)").Trim()
$zip = Join-Path $ArtifactDir "PocketLedger-v$version-win64-portable.zip"
$setup = Join-Path $ArtifactDir "PocketLedger-v$version-win64-setup.exe"
$sums = Join-Path $ArtifactDir 'SHA256SUMS.txt'
$notes = Join-Path $ArtifactDir 'RELEASE_NOTES.md'
foreach ($file in @($zip, $setup, $sums, $notes)) {
    if (-not (Test-Path $file)) { throw "Missing artifact: $file" }
}

Write-Host 'Verifying SHA256SUMS.txt...'
$expected = @{}
foreach ($line in Get-Content $sums) {
    if ($line -match '^([0-9a-f]{64})\s{2}(.+)$') {
        $expected[$Matches[2]] = $Matches[1]
    }
}
if ($expected.Count -ne 2) { throw "Expected two checksum entries, found $($expected.Count)." }
foreach ($name in $expected.Keys) {
    $path = Join-Path $ArtifactDir $name
    if (-not (Test-Path $path)) { throw "Checksum references missing file: $name" }
    $actual = (Get-FileHash -Algorithm SHA256 -Path $path).Hash.ToLowerInvariant()
    if ($actual -ne $expected[$name]) { throw "Checksum mismatch for $name" }
}
$notesText = Get-Content $notes -Raw
if ($notesText -notmatch [regex]::Escape($version)) { throw 'Release notes are missing the version.' }

$setupVersion = (Get-Item $setup).VersionInfo.FileVersion
Write-Host "Installer file version: $setupVersion"

function Invoke-Setup($path, [string[]] $arguments, $step) {
    $process = Start-Process -FilePath $path -ArgumentList $arguments -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "$step failed with exit code $($process.ExitCode)"
    }
}

function Launch-And-Stop($exe, $localAppData) {
    $env:QT_QPA_PLATFORM = 'offscreen'
    $env:LOCALAPPDATA = $localAppData
    Remove-Item Env:POCKET_LEDGER_DB -ErrorAction SilentlyContinue
    $process = Start-Process -FilePath $exe -PassThru
    Start-Sleep -Seconds 8
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        Start-Sleep -Milliseconds 800
    }
}

function Write-Sentinel($dbPath, $value) {
    & $python -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE IF NOT EXISTS release_verify (value TEXT)'); c.execute('DELETE FROM release_verify'); c.execute('INSERT INTO release_verify VALUES (?)', (sys.argv[2],)); c.commit(); c.close()" $dbPath $value
    if ($LASTEXITCODE -ne 0) { throw "Could not write sentinel to $dbPath" }
}

function Read-Sentinel($dbPath) {
    $result = & $python -c "import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute('SELECT value FROM release_verify').fetchone()[0])" $dbPath
    if ($LASTEXITCODE -ne 0) { throw "Could not read sentinel from $dbPath" }
    return $result.Trim()
}

# --- Portable ZIP -----------------------------------------------------------
$portableRoot = Join-Path $WorkDir 'portable-clean'
New-Item -ItemType Directory -Path $portableRoot -Force | Out-Null
Expand-Archive -Path $zip -DestinationPath $portableRoot -Force
if (-not (Test-Path (Join-Path $portableRoot 'PocketLedger.exe'))) {
    throw 'Portable ZIP did not contain PocketLedger.exe at its root.'
}
if (-not (Test-Path (Join-Path $portableRoot 'portable.marker'))) {
    throw 'Portable ZIP did not contain portable.marker.'
}
$portableFakeLocalAppData = Join-Path $WorkDir 'portable-localappdata'
New-Item -ItemType Directory -Path $portableFakeLocalAppData -Force | Out-Null
Launch-And-Stop (Join-Path $portableRoot 'PocketLedger.exe') $portableFakeLocalAppData
$portableDb = Join-Path $portableRoot 'data\pocket_ledger.db'
if (-not (Test-Path $portableDb)) { throw 'Portable run did not create data\\pocket_ledger.db beside the EXE.' }
if (Get-ChildItem $portableFakeLocalAppData -Recurse -Filter 'pocket_ledger.db' -ErrorAction SilentlyContinue) {
    throw 'Portable run wrote user data into LOCALAPPDATA.'
}
Write-Host "Portable OK: $portableDb"

# --- Installed build --------------------------------------------------------
$fakeLocalAppData = Join-Path $WorkDir 'installed-localappdata'
$userDataDir = Join-Path $fakeLocalAppData 'Pocket Ledger\data'
New-Item -ItemType Directory -Path $userDataDir -Force | Out-Null
$userDb = Join-Path $userDataDir 'pocket_ledger.db'
$sentinel = 'preserve-me-0.4.0'
Write-Sentinel $userDb $sentinel

$installDir = Join-Path $WorkDir 'installed-app'
New-Item -ItemType Directory -Path $installDir -Force | Out-Null
Write-Host 'Running clean install...'
Invoke-Setup $setup @('/VERYSILENT', '/NORESTART', '/NOICONS', "/DIR=$installDir") 'Clean install'
$installedExe = Join-Path $installDir 'PocketLedger.exe'
if (-not (Test-Path $installedExe)) { throw 'Installer did not place PocketLedger.exe in the target directory.' }

function Get-InstallerEntry {
    Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall' -ErrorAction SilentlyContinue |
        ForEach-Object { Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue } |
        Where-Object { $_.DisplayName -like 'Pocket Ledger*' }
}
if (-not (Get-InstallerEntry)) { throw 'No Apps & Features uninstall entry was registered.' }

Launch-And-Stop $installedExe $fakeLocalAppData
if (-not (Test-Path $userDb)) { throw 'Installed run did not use the LOCALAPPDATA database.' }
if (Get-ChildItem $installDir -Recurse -Filter 'pocket_ledger.db' -ErrorAction SilentlyContinue) {
    throw 'Installed run wrote user data inside the installation directory.'
}
if ((Read-Sentinel $userDb) -ne $sentinel) { throw 'Installed run did not preserve pre-existing user data.' }

Write-Host 'Running upgrade over the existing install...'
Invoke-Setup $setup @('/VERYSILENT', '/NORESTART', '/NOICONS', "/DIR=$installDir") 'Upgrade'
if (-not (Test-Path $installedExe)) { throw 'Upgrade removed PocketLedger.exe.' }
if ((Read-Sentinel $userDb) -ne $sentinel) { throw 'Upgrade deleted or changed user data.' }

$uninstaller = Get-ChildItem $installDir -Filter 'unins*.exe' | Select-Object -First 1
if (-not $uninstaller) { throw 'Installer did not create an uninstaller.' }
Write-Host 'Running uninstall...'
Invoke-Setup $uninstaller.FullName @('/VERYSILENT', '/NORESTART') 'Uninstall'
if (Test-Path $installedExe) { throw 'Uninstall left PocketLedger.exe behind.' }
if ((Read-Sentinel $userDb) -ne $sentinel) { throw 'Uninstall deleted or changed user data.' }
if (Get-InstallerEntry) { throw 'Uninstall left an Apps & Features entry behind.' }

Write-Host "Uninstall preserved user data: $userDb"
Write-Host 'Windows release verification passed.'
