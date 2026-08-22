param(
    [Parameter(Mandatory = $true)]
    [string]$PackageDir,

    [string]$Version = "v0.1.2-rc2",

    [string]$OutputDir = (Join-Path (Get-Location) "outputs"),

    [string]$MakensisPath = "",

    [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RequiredPath {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Path not found: $Path"
    }

    return (Resolve-Path -LiteralPath $Path).Path
}

function Get-ViVersion {
    param([string]$ReleaseVersion)

    $normalized = $ReleaseVersion -replace "^[vV]", ""
    if ($normalized -match "^([0-9]+)\.([0-9]+)\.([0-9]+)") {
        return "$($Matches[1]).$($Matches[2]).$($Matches[3]).0"
    }

    return "0.0.0.0"
}

function Find-Makensis {
    param([string]$ExplicitPath)

    if (-not [string]::IsNullOrWhiteSpace($ExplicitPath)) {
        return Resolve-RequiredPath -Path $ExplicitPath
    }

    $command = Get-Command makensis.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    foreach ($candidate in @(
        "${env:ProgramFiles}\NSIS\makensis.exe",
        "${env:ProgramFiles(x86)}\NSIS\makensis.exe"
    )) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    throw "NSIS makensis.exe was not found. Install NSIS or pass -MakensisPath."
}

$packagePath = Resolve-RequiredPath -Path $PackageDir

$requiredFiles = @(
    "bitstard.exe",
    "bitstar-cli.exe",
    "bitstar-util.exe",
    "bitstar.exe",
    "sqlite3.dll",
    "BitStar-Launcher.bat",
    "BitStar-Launcher.ps1",
    "Show-BitStar-Wallet-Address.bat",
    "Open-BitStar-Console.bat",
    "Start-BitStar-Node.bat",
    "Check-BitStar-Status.bat",
    "Stop-BitStar-Node.bat"
)

$missing = @()
foreach ($file in $requiredFiles) {
    $path = Join-Path $packagePath $file
    if (-not (Test-Path -LiteralPath $path)) {
        $missing += $file
    }
}

if ($missing.Count -gt 0) {
    throw "Package is missing required files: $($missing -join ', ')"
}

$scriptPath = Resolve-RequiredPath -Path (Join-Path $PSScriptRoot "..\windows\installer\BitStar-Launcher-Installer.nsi")
$outputPath = Resolve-RequiredPath -Path $OutputDir
$safeVersion = $Version -replace "[^A-Za-z0-9_.-]", "_"
$installerPath = Join-Path $outputPath "BitStar_Core_Setup_$safeVersion.exe"
$viVersion = Get-ViVersion -ReleaseVersion $Version

Write-Host "PACKAGE_OK $packagePath"
Write-Host "VERSION $Version"
Write-Host "VI_VERSION $viVersion"
Write-Host "INSTALLER $installerPath"

if ($CheckOnly) {
    Write-Host "CHECK_ONLY_OK"
    exit 0
}

$makensis = Find-Makensis -ExplicitPath $MakensisPath

$args = @(
    "/DVERSION=$Version",
    "/DVI_VERSION=$viVersion",
    "/DPACKAGE_DIR=$packagePath",
    "/DOUT_FILE=$installerPath",
    $scriptPath
)

& $makensis @args
if ($LASTEXITCODE -ne 0) {
    throw "makensis failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path -LiteralPath $installerPath)) {
    throw "Installer was not created: $installerPath"
}

$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $installerPath
Write-Host "INSTALLER_SHA256 $($hash.Hash.ToLowerInvariant())  $installerPath"
