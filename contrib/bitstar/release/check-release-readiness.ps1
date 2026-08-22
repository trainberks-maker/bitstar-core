param(
    [string]$ReleaseDir = ".",
    [string]$Manifest = "SHA256SUMS",
    [switch]$AllowUnsignedBootstrap
)

$ErrorActionPreference = "Stop"

function Fail($Message) {
    Write-Host "FAIL    $Message"
    $script:failed = $true
}

function Warn($Message) {
    Write-Host "WARN    $Message"
    $script:warned = $true
}

function Pass($Message) {
    Write-Host "OK      $Message"
}

$failed = $false
$warned = $false
$releasePath = Resolve-Path -LiteralPath $ReleaseDir
$manifestPath = Join-Path $releasePath $Manifest
$signaturePath = "$manifestPath.asc"

Write-Host "BitStar release readiness check"
Write-Host "Release directory: $releasePath"

if (!(Test-Path -LiteralPath $manifestPath)) {
    Fail "manifest not found: $manifestPath"
    exit 1
}

Pass "manifest present: $Manifest"

$entries = @()
Get-Content -LiteralPath $manifestPath | ForEach-Object {
    $line = $_.Trim()
    if ($line.Length -eq 0 -or $line.StartsWith("#")) {
        return
    }

    $parts = $line -split "\s+", 2
    if ($parts.Count -ne 2 -or $parts[0] -notmatch "^[a-fA-F0-9]{64}$") {
        Fail "invalid manifest line: $line"
        return
    }

    $name = $parts[1].Trim()
    if ($name.StartsWith("*")) {
        $name = $name.Substring(1)
    }

    $entries += [PSCustomObject]@{
        Hash = $parts[0].ToLowerInvariant()
        Name = $name
    }
}

if ($entries.Count -eq 0) {
    Fail "manifest contains no artifact entries"
}

foreach ($entry in $entries) {
    $artifactPath = Join-Path $releasePath $entry.Name
    if (!(Test-Path -LiteralPath $artifactPath)) {
        Fail "artifact missing: $($entry.Name)"
        continue
    }

    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $artifactPath).Hash.ToLowerInvariant()
    if ($actual -ne $entry.Hash) {
        Fail "checksum mismatch: $($entry.Name)"
    } else {
        Pass "checksum verified: $($entry.Name)"
    }
}

$gpg = Get-Command gpg -ErrorAction SilentlyContinue
if (!$gpg) {
    Warn "gpg not found; install GnuPG or Gpg4win before production signing"
} else {
    Pass "gpg available: $($gpg.Source)"
}

if (!(Test-Path -LiteralPath $signaturePath)) {
    if ($AllowUnsignedBootstrap) {
        Warn "signature missing: $Manifest.asc; allowed only for bootstrap status"
    } else {
        Fail "signature missing: $Manifest.asc"
    }
} elseif (!$gpg) {
    Fail "signature exists but cannot be verified because gpg is missing"
} else {
    & $gpg.Source --verify $signaturePath $manifestPath
    if ($LASTEXITCODE -ne 0) {
        Fail "GPG signature verification failed"
    } else {
        Pass "GPG signature verified: $Manifest.asc"
    }
}

if ($failed) {
    Write-Host "Result: not production-ready."
    exit 1
}

if ($warned) {
    Write-Host "Result: bootstrap-verifiable only, not production signed."
    exit 0
}

Write-Host "Result: release artifacts are signed and checksum verified."
