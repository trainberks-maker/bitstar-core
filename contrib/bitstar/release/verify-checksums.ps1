param(
    [string]$Manifest = ".\SHA256SUMS"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path -LiteralPath $Manifest)) {
    Write-Error "Manifest not found: $Manifest"
    exit 2
}

$manifestDir = Split-Path -Parent (Resolve-Path -LiteralPath $Manifest)
if ([string]::IsNullOrWhiteSpace($manifestDir)) {
    $manifestDir = (Get-Location).Path
}

$failed = $false
$checked = 0

Get-Content -LiteralPath $Manifest | ForEach-Object {
    $line = $_.Trim()
    if ($line.Length -eq 0 -or $line.StartsWith("#")) {
        return
    }

    $parts = $line -split "\s+", 2
    if ($parts.Count -ne 2 -or $parts[0] -notmatch "^[a-fA-F0-9]{64}$") {
        Write-Host "INVALID $line"
        $script:failed = $true
        return
    }

    $expected = $parts[0].ToLowerInvariant()
    $fileName = $parts[1].Trim()
    if ($fileName.StartsWith("*")) {
        $fileName = $fileName.Substring(1)
    }

    $path = Join-Path $manifestDir $fileName
    if (!(Test-Path -LiteralPath $path)) {
        Write-Host "MISSING $fileName"
        $script:failed = $true
        return
    }

    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    $script:checked += 1
    if ($actual -eq $expected) {
        Write-Host "OK      $fileName"
    } else {
        Write-Host "FAILED  $fileName"
        $script:failed = $true
    }
}

if ($checked -eq 0) {
    Write-Error "No checksum entries were checked."
    exit 2
}

if ($failed) {
    exit 1
}

Write-Host "All $checked checksum entries verified."
