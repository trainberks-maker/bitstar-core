param(
    [string]$GpgKey = "",
    [string]$Output = ".\bitstar-release-key.asc"
)

$ErrorActionPreference = "Stop"

function Resolve-GpgPath {
    $gpg = Get-Command gpg -ErrorAction SilentlyContinue
    if ($gpg) {
        return $gpg.Source
    }

    $programFilesX86 = ${env:ProgramFiles(x86)}
    $candidates = @()

    if (![string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
        $candidates += @(
            (Join-Path $env:ProgramFiles "Git\usr\bin\gpg.exe"),
            (Join-Path $env:ProgramFiles "Git\mingw64\bin\gpg.exe"),
            (Join-Path $env:ProgramFiles "GnuPG\bin\gpg.exe"),
            (Join-Path $env:ProgramFiles "Gpg4win\bin\gpg.exe")
        )
    }

    if (![string]::IsNullOrWhiteSpace($programFilesX86)) {
        $candidates += @(
            (Join-Path $programFilesX86 "GnuPG\bin\gpg.exe"),
            (Join-Path $programFilesX86 "Gpg4win\bin\gpg.exe")
        )
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

if ([string]::IsNullOrWhiteSpace($GpgKey)) {
    Write-Error "Pass -GpgKey with the BitStar release key fingerprint, long key id, or user id."
    exit 2
}

$gpgPath = Resolve-GpgPath
if (!$gpgPath) {
    Write-Error "gpg was not found. Install GnuPG/Gpg4win or use Git for Windows GPG."
    exit 2
}

& $gpgPath --list-keys --keyid-format LONG $GpgKey
if ($LASTEXITCODE -ne 0) {
    Write-Error "Release public key not found: $GpgKey"
    exit $LASTEXITCODE
}

$outputPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Output)
$outputDir = Split-Path -Parent $outputPath
if (![string]::IsNullOrWhiteSpace($outputDir) -and !(Test-Path -LiteralPath $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

& $gpgPath --armor --export --output $outputPath $GpgKey
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to export public release key."
    exit $LASTEXITCODE
}

Write-Host "Wrote public release key: $Output"
Write-Host "Release key fingerprint:"
& $gpgPath --fingerprint --keyid-format LONG $GpgKey

Write-Host ""
Write-Host "Safety: this exports only the public key. Never upload or paste the secret release key or passphrase."
