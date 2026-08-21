param(
    [string[]]$Artifacts = @(),
    [string]$Output = ".\SHA256SUMS",
    [string]$GpgKey = "",
    [switch]$NoSign
)

$ErrorActionPreference = "Stop"

if ($Artifacts.Count -eq 0) {
    $Artifacts = Get-ChildItem -File |
        Where-Object { $_.Name -match "^BitStar_.*(\.zip|\.tar\.gz)$" } |
        Sort-Object Name |
        ForEach-Object { $_.FullName }
}

$Artifacts = @(
    $Artifacts |
        ForEach-Object { $_ -split "," } |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_.Length -gt 0 }
)

if ($Artifacts.Count -eq 0) {
    Write-Error "No artifacts provided. Pass package paths or run from a folder containing BitStar release packages."
    exit 2
}

$manifestLines = @()
foreach ($artifact in $Artifacts) {
    if (!(Test-Path -LiteralPath $artifact)) {
        Write-Error "Artifact not found: $artifact"
        exit 2
    }

    $resolved = Resolve-Path -LiteralPath $artifact
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $resolved).Hash.ToLowerInvariant()
    $name = Split-Path -Leaf $resolved
    $manifestLines += "$hash  $name"
}

$outputPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Output)
$outputDir = Split-Path -Parent $outputPath
if (![string]::IsNullOrWhiteSpace($outputDir) -and !(Test-Path -LiteralPath $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

$manifestLines | Set-Content -Encoding ascii -LiteralPath $outputPath
Write-Host "Wrote $Output with $($manifestLines.Count) artifact checksum(s)."

if ($NoSign) {
    Write-Host "Skipped GPG signing because -NoSign was set."
    exit 0
}

$gpg = Get-Command gpg -ErrorAction SilentlyContinue
if (!$gpg) {
    Write-Error "gpg was not found. Install GnuPG or run with -NoSign to create only SHA256SUMS."
    exit 2
}

$signaturePath = "$outputPath.asc"
$gpgArgs = @("--armor", "--detach-sign", "--output", $signaturePath)
if (![string]::IsNullOrWhiteSpace($GpgKey)) {
    $gpgArgs += @("--local-user", $GpgKey)
}
$gpgArgs += $outputPath

& $gpg.Source @gpgArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "GPG signing failed."
    exit $LASTEXITCODE
}

& $gpg.Source --verify $signaturePath $outputPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "GPG signature self-check failed."
    exit $LASTEXITCODE
}

Write-Host "Wrote detached signature: $Output.asc"
