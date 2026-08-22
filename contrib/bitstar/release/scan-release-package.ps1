param(
    [string]$ReleaseDir = ".",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Artifacts = @()
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

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

function Test-TextEntry($Name) {
    return $Name -match "(?i)\.(md|txt|conf|service|timer|sh|bat|ps1|json|yml|yaml|ini|env|log)$"
}

function Test-EntryPath($ArtifactName, $EntryName) {
    $normalized = $EntryName -replace "\\", "/"
    $forbiddenPathPattern = "(?i)(^|/)(wallet\.dat|blocks|chainstate|indexes|wallets|debug\.log|mempool\.dat|peers\.dat|banlist\.dat|\.cookie|\.ssh|id_rsa|id_dsa|id_ecdsa|id_ed25519|authorized_keys|known_hosts)(/|$)|\.(pem|p12|pfx)$"

    if ($normalized -match $forbiddenPathPattern) {
        Fail "$ArtifactName contains private node, wallet, or credential path: $normalized"
    }
}

function Test-TextContent($ArtifactName, $EntryName, $Content) {
    if ($Content -match "-----BEGIN (OPENSSH|RSA|DSA|EC|.*PRIVATE) PRIVATE KEY-----") {
        Fail "$ArtifactName entry $EntryName contains private key material"
    }

    if ($EntryName -match "(?i)\.(md|txt)$") {
        return
    }

    $strictChecks = @(
        @{
            Pattern = "(?im)^\s*(rpcpassword|rpcauth)\s*=\s*[^#\s]+"
            Message = "hard-coded RPC credential"
        },
        @{
            Pattern = "(?im)^\s*(github_token|digitalocean_token|cloudflare_api_token|openai_api_key|api_key|secret_key|password)\s*=\s*[^#\s]+"
            Message = "hard-coded token or password"
        },
        @{
            Pattern = "(?im)^\s*rpcbind\s*=\s*(0\.0\.0\.0|\*)"
            Message = "unsafe public RPC bind"
        },
        @{
            Pattern = "(?im)^\s*rpcallowip\s*=\s*(0\.0\.0\.0/0|::/0|\*)"
            Message = "unsafe public RPC allowlist"
        }
    )

    foreach ($check in $strictChecks) {
        if ($Content -match $check.Pattern) {
            Fail "$ArtifactName entry $EntryName contains $($check.Message)"
        }
    }
}

function Read-ZipTextEntry($ZipEntry) {
    $stream = $ZipEntry.Open()
    try {
        $reader = [System.IO.StreamReader]::new($stream)
        try {
            return $reader.ReadToEnd()
        } finally {
            $reader.Dispose()
        }
    } finally {
        $stream.Dispose()
    }
}

function Scan-Zip($Artifact) {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($Artifact.FullName)
    try {
        foreach ($entry in $zip.Entries) {
            Test-EntryPath $Artifact.Name $entry.FullName
            if ($entry.Length -gt 0 -and $entry.Length -le 1048576 -and (Test-TextEntry $entry.FullName)) {
                $content = Read-ZipTextEntry $entry
                Test-TextContent $Artifact.Name $entry.FullName $content
            }
        }
    } finally {
        $zip.Dispose()
    }

    Pass "package hygiene scan completed: $($Artifact.Name)"
}

function Scan-TarGz($Artifact) {
    $entries = & tar -tzf $Artifact.FullName
    if ($LASTEXITCODE -ne 0) {
        Fail "could not list archive: $($Artifact.Name)"
        return
    }

    foreach ($entry in $entries) {
        Test-EntryPath $Artifact.Name $entry
        if (Test-TextEntry $entry) {
            $content = & tar -xOzf $Artifact.FullName $entry 2>$null | Out-String
            if ($LASTEXITCODE -eq 0 -and $content.Length -le 1048576) {
                Test-TextContent $Artifact.Name $entry $content
            }
        }
    }

    Pass "package hygiene scan completed: $($Artifact.Name)"
}

$failed = $false
$warned = $false
$releasePath = (Resolve-Path -LiteralPath $ReleaseDir).Path
$normalizedArtifacts = @()
foreach ($artifact in $Artifacts) {
    foreach ($part in ($artifact -split ",")) {
        $name = $part.Trim().Trim('"').Trim("'")
        if ($name.Length -gt 0) {
            $normalizedArtifacts += $name
        }
    }
}
$Artifacts = $normalizedArtifacts

Write-Host "BitStar release package hygiene scan"
Write-Host "Release directory: $releasePath"

if ($Artifacts.Count -eq 0) {
    $artifactFiles = Get-ChildItem -LiteralPath $releasePath -File |
        Where-Object { $_.Name -match "(?i)\.(zip|tar\.gz|tgz)$" }
} else {
    $artifactFiles = foreach ($artifact in $Artifacts) {
        $path = Join-Path $releasePath $artifact
        if (Test-Path -LiteralPath $path) {
            Get-Item -LiteralPath $path
        } else {
            Fail "artifact not found: $artifact"
        }
    }
}

if (!$artifactFiles -or $artifactFiles.Count -eq 0) {
    Fail "no release archives found"
}

foreach ($artifact in $artifactFiles) {
    if ($artifact.Name -match "(?i)\.zip$") {
        Scan-Zip $artifact
    } elseif ($artifact.Name -match "(?i)\.(tar\.gz|tgz)$") {
        Scan-TarGz $artifact
    } else {
        Warn "skipping unsupported artifact: $($artifact.Name)"
    }
}

if ($failed) {
    Write-Host "Result: package hygiene scan failed."
    exit 1
}

if ($warned) {
    Write-Host "Result: package hygiene scan completed with warnings."
    exit 0
}

Write-Host "Result: package hygiene scan passed."
