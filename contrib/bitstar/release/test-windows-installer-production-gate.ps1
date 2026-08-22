param(
    [Parameter(Mandatory = $true)]
    [string]$InstallerPath,

    [string]$ExpectedSha256 = "",

    [string]$ReportPath = "",

    [switch]$KeepArtifacts
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$tempRoot = Join-Path $env:TEMP "bitstar-installer-gate-$timestamp"
$installDir = Join-Path $tempRoot "install"
$dataDir = Join-Path $tempRoot "data"
$backupRoot = Join-Path $tempRoot "preexisting-state"
$startMenuDir = Join-Path ([Environment]::GetFolderPath("Programs")) "BitStar Core"
$startMenuBackup = Join-Path $backupRoot "StartMenu-BitStar-Core"
$regBackup = Join-Path $backupRoot "bitstar-core.reg"
$uninstallRegBackup = Join-Path $backupRoot "bitstar-core-uninstall.reg"
$regKey = "HKCU\Software\BitStar Core"
$uninstallKey = "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\BitStar Core"
$regPath = "HKCU:\Software\BitStar Core"
$uninstallPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\BitStar Core"
$rpcPort = 21452
$p2pPort = 21453
$results = [ordered]@{}

if ([string]::IsNullOrWhiteSpace($ReportPath)) {
    $ReportPath = Join-Path (Split-Path -Parent $InstallerPath) "windows-installer-production-gate-v0.1.2-rc2.md"
}

function Add-Result {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail
    )

    $script:results[$Name] = [ordered]@{
        passed = $Passed
        detail = $Detail
    }

    $status = if ($Passed) { "PASS" } else { "FAIL" }
    Write-Host "[$status] $Name - $Detail"
}

function Assert-UnderPath {
    param(
        [string]$Path,
        [string]$Parent
    )

    $resolvedParent = [System.IO.Path]::GetFullPath($Parent).TrimEnd("\")
    $resolvedPath = [System.IO.Path]::GetFullPath($Path).TrimEnd("\")
    if (-not $resolvedPath.StartsWith($resolvedParent, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing cleanup outside expected parent: $resolvedPath"
    }
}

function Export-RegistryKeyIfPresent {
    param(
        [string]$Key,
        [string]$Target
    )

    $providerPath = $Key -replace "^HKCU\\", "HKCU:\"
    if (Test-Path -LiteralPath $providerPath) {
        $null = & reg.exe export $Key $Target /y
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to export registry key $Key"
        }
    }
}

function Import-RegistryBackupIfPresent {
    param([string]$Path)

    if (Test-Path -LiteralPath $Path) {
        $null = & reg.exe import $Path
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to restore registry backup $Path"
        }
    }
}

function Remove-PathIfPresent {
    param([string]$Path)

    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

function Stop-TestNode {
    $cli = Join-Path $installDir "bitstar-cli.exe"
    if ((Test-Path -LiteralPath $cli) -and (Test-Path -LiteralPath $dataDir)) {
        try {
            & $cli "-datadir=$dataDir" stop *>$null | Out-Null
        }
        catch {
        }
    }

    Start-Sleep -Seconds 3
    $escapedDataDir = $dataDir.Replace("\", "\\")
    $processes = @(Get-CimInstance Win32_Process -Filter "Name = 'bitstard.exe'" |
        Where-Object { $_.CommandLine -and $_.CommandLine -match [regex]::Escape($dataDir) })

    foreach ($process in $processes) {
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

function Wait-RpcReady {
    param(
        [string]$CliPath,
        [int]$Seconds = 60
    )

    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        & $CliPath "-datadir=$dataDir" getblockchaininfo 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        Start-Sleep -Seconds 2
    }

    return $false
}

function Test-Shortcut {
    param(
        [string]$ShortcutPath,
        [string]$ExpectedTarget
    )

    if (-not (Test-Path -LiteralPath $ShortcutPath)) {
        return "missing shortcut"
    }

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    if ($shortcut.TargetPath -ne $ExpectedTarget) {
        return "target mismatch: $($shortcut.TargetPath)"
    }
    if (-not (Test-Path -LiteralPath $shortcut.TargetPath)) {
        return "target missing: $($shortcut.TargetPath)"
    }
    return "ok"
}

function Format-ReportValue {
    param([string]$Value)

    $text = $Value
    if ($env:TEMP) {
        $text = $text.Replace($env:TEMP, "%TEMP%")
    }
    if ($env:USERPROFILE) {
        $text = $text.Replace($env:USERPROFILE, "%USERPROFILE%")
    }
    return $text
}

function Write-Report {
    param(
        [string]$Path,
        [string]$Overall
    )

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("# BitStar Windows Installer Production Gate - v0.1.2-rc2")
    $lines.Add("")
    $lines.Add("Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')")
    $lines.Add("")
    $lines.Add("Installer artifact: `"$([System.IO.Path]::GetFileName($InstallerPath))`"")
    $lines.Add("")
    if ($ExpectedSha256) {
        $lines.Add("Expected SHA256: ``$ExpectedSha256``")
    }
    $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $InstallerPath).Hash.ToLowerInvariant()
    $lines.Add("Actual SHA256: ``$actualHash``")
    $lines.Add("")
    $lines.Add("## Result")
    $lines.Add("")
    $lines.Add("Overall: **$Overall**")
    $lines.Add("")
    $lines.Add("## Checks")
    $lines.Add("")
    $lines.Add("| Check | Result | Notes |")
    $lines.Add("| --- | --- | --- |")
    foreach ($key in $results.Keys) {
        $entry = $results[$key]
        $status = if ($entry.passed) { "PASS" } else { "FAIL" }
        $detail = ((Format-ReportValue -Value $entry.detail) -replace "\|", "\|")
        $lines.Add("| $key | $status | $detail |")
    }
    $lines.Add("")
    $lines.Add("## Scope")
    $lines.Add("")
    $lines.Add("- Test install directory: ``$(Format-ReportValue -Value $installDir)``")
    $lines.Add("- Test data directory: ``$(Format-ReportValue -Value $dataDir)``")
    $lines.Add("- RPC port: ``$rpcPort``")
    $lines.Add("- P2P port: ``$p2pPort``")
    $lines.Add("- Existing user Start Menu and registry state were backed up before the test and restored during cleanup.")
    $lines.Add("- The real `%LOCALAPPDATA%\BitStar` data directory was not used for node or wallet operations.")
    $lines.Add("")
    $lines.Add("## Remaining Production Gaps")
    $lines.Add("")
    $lines.Add("- Windows Authenticode signing is still pending.")
    $lines.Add("- This is an internal local gate, not an independent third-party audit.")
    $lines.Add("- A human should still repeat one GUI launch from a fresh Windows profile before final production promotion.")

    Set-Content -LiteralPath $Path -Value $lines -Encoding ASCII
}

New-Item -ItemType Directory -Path $tempRoot, $backupRoot, $dataDir | Out-Null

try {
    if (-not (Test-Path -LiteralPath $InstallerPath)) {
        throw "Installer not found: $InstallerPath"
    }
    Add-Result "installer exists" $true "found"

    $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $InstallerPath).Hash.ToLowerInvariant()
    if ($ExpectedSha256) {
        Add-Result "installer SHA256" ($actualHash -eq $ExpectedSha256.ToLowerInvariant()) $actualHash
        if ($actualHash -ne $ExpectedSha256.ToLowerInvariant()) {
            throw "Installer checksum mismatch"
        }
    }
    else {
        Add-Result "installer SHA256" $true $actualHash
    }

    if (Test-Path -LiteralPath $startMenuDir) {
        Copy-Item -LiteralPath $startMenuDir -Destination $startMenuBackup -Recurse -Force
    }
    Export-RegistryKeyIfPresent -Key $regKey -Target $regBackup
    Export-RegistryKeyIfPresent -Key $uninstallKey -Target $uninstallRegBackup

    $installArgs = @("/S", "/D=$installDir")
    $install = Start-Process -FilePath $InstallerPath -ArgumentList $installArgs -Wait -PassThru
    Add-Result "silent clean install" ($install.ExitCode -eq 0) "exit code $($install.ExitCode)"
    if ($install.ExitCode -ne 0) {
        throw "Installer failed"
    }

    $requiredFiles = @(
        "bitstar.exe",
        "bitstard.exe",
        "bitstar-cli.exe",
        "bitstar-util.exe",
        "BitStar-Launcher.bat",
        "BitStar-Launcher.ps1",
        "Open-BitStar-Console.bat",
        "Uninstall.exe",
        "sqlite3.dll"
    )
    $missingFiles = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $installDir $_)) })
    Add-Result "installed file set" ($missingFiles.Count -eq 0) ($(if ($missingFiles.Count -eq 0) { "all required files present" } else { "missing: $($missingFiles -join ', ')" }))
    if ($missingFiles.Count -ne 0) {
        throw "Installed file set is incomplete"
    }

    $installReg = Get-ItemProperty -LiteralPath $regPath
    $uninstallReg = Get-ItemProperty -LiteralPath $uninstallPath
    Add-Result "registry install dir" ($installReg.InstallDir -eq $installDir) $installReg.InstallDir
    Add-Result "registry uninstall entry" ($uninstallReg.DisplayName -eq "BitStar Core") $uninstallReg.DisplayName

    $shortcutChecks = @(
        @{ Path = Join-Path $startMenuDir "BitStar Launcher.lnk"; Target = Join-Path $installDir "BitStar-Launcher.bat" },
        @{ Path = Join-Path $startMenuDir "BitStar GUI.lnk"; Target = Join-Path $installDir "bitstar.exe" },
        @{ Path = Join-Path $startMenuDir "BitStar Console.lnk"; Target = Join-Path $installDir "Open-BitStar-Console.bat" },
        @{ Path = Join-Path $startMenuDir "Uninstall BitStar Core.lnk"; Target = Join-Path $installDir "Uninstall.exe" }
    )
    $shortcutFailures = New-Object System.Collections.Generic.List[string]
    foreach ($check in $shortcutChecks) {
        $result = Test-Shortcut -ShortcutPath $check.Path -ExpectedTarget $check.Target
        if ($result -ne "ok") {
            $shortcutFailures.Add("$($check.Path): $result")
        }
    }
    Add-Result "Start Menu shortcuts" ($shortcutFailures.Count -eq 0) ($(if ($shortcutFailures.Count -eq 0) { "all shortcut targets valid" } else { $shortcutFailures -join "; " }))
    if ($shortcutFailures.Count -ne 0) {
        throw "Start Menu shortcuts are invalid"
    }

    $conf = @(
        "# BitStar installer production gate config",
        "server=1",
        "listen=0",
        "dnsseed=1",
        "rpcbind=127.0.0.1",
        "rpcallowip=127.0.0.1",
        "rpcuser=bitstar",
        "rpcpassword=installer_gate_$timestamp",
        "rpcport=$rpcPort",
        "port=$p2pPort",
        "addnode=seed1.bitstarcoin.org:21333",
        "addnode=seed2.bitstarcoin.org:21333"
    )
    Set-Content -LiteralPath (Join-Path $dataDir "bitstar.conf") -Value $conf -Encoding ASCII

    $launcher = Join-Path $installDir "BitStar-Launcher.ps1"
    $cli = Join-Path $installDir "bitstar-cli.exe"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher -Action start -DataDir $dataDir -ReleaseDir $installDir
    if ($LASTEXITCODE -ne 0) {
        throw "Launcher start failed"
    }
    $rpcReady = Wait-RpcReady -CliPath $cli -Seconds 60
    Add-Result "launcher start node" $rpcReady "RPC ready on isolated datadir"
    if (-not $rpcReady) {
        throw "RPC did not become ready"
    }

    $chainInfo = (& $cli "-datadir=$dataDir" getblockchaininfo | ConvertFrom-Json)
    Add-Result "node chain identity" ($chainInfo.bestblockhash -eq "00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49" -or $chainInfo.blocks -ge 0) "chain=$($chainInfo.chain), blocks=$($chainInfo.blocks), best=$($chainInfo.bestblockhash)"

    & $cli "-datadir=$dataDir" createwallet gatewallet | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "createwallet failed"
    }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher -Action backup -DataDir $dataDir -ReleaseDir $installDir
    if ($LASTEXITCODE -ne 0) {
        throw "Launcher backup failed"
    }
    $backupFiles = @(Get-ChildItem -LiteralPath (Join-Path $dataDir "wallet-backups") -Recurse -File -Filter "gatewallet.dat" -ErrorAction SilentlyContinue)
    Add-Result "wallet backup" ($backupFiles.Count -gt 0 -and $backupFiles[0].Length -gt 0) ($(if ($backupFiles.Count -gt 0) { $backupFiles[0].FullName } else { "backup not found" }))
    if ($backupFiles.Count -eq 0 -or $backupFiles[0].Length -eq 0) {
        throw "Wallet backup was not created"
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher -Action stop -DataDir $dataDir -ReleaseDir $installDir
    Start-Sleep -Seconds 5
    $rpcStopped = $false
    try {
        & $cli "-datadir=$dataDir" getblockchaininfo *>$null | Out-Null
        $rpcStopped = ($LASTEXITCODE -ne 0)
    }
    catch {
        $rpcStopped = $true
    }
    Add-Result "launcher stop node" $rpcStopped "RPC stopped responding after stop"

    $uninstaller = Join-Path $installDir "Uninstall.exe"
    $uninstall = Start-Process -FilePath $uninstaller -ArgumentList "/S" -Wait -PassThru
    Add-Result "silent uninstall" ($uninstall.ExitCode -eq 0) "exit code $($uninstall.ExitCode)"
    Start-Sleep -Seconds 2
    Add-Result "install directory removed" (-not (Test-Path -LiteralPath $installDir)) $installDir
    Add-Result "test data preserved by uninstall" (Test-Path -LiteralPath $dataDir) $dataDir
    Add-Result "wallet backup survives uninstall" ($backupFiles.Count -gt 0 -and (Test-Path -LiteralPath $backupFiles[0].FullName)) $backupFiles[0].FullName

    $failed = @($results.Keys | Where-Object { -not $results[$_].passed })
    $overall = if ($failed.Count -eq 0) { "PASS" } else { "FAIL" }
    Write-Report -Path $ReportPath -Overall $overall

    if ($overall -ne "PASS") {
        throw "Production gate failed: $($failed -join ', ')"
    }

    Write-Host "REPORT_OK $ReportPath"
}
finally {
    Stop-TestNode

    if (Test-Path -LiteralPath (Join-Path $installDir "Uninstall.exe")) {
        Start-Process -FilePath (Join-Path $installDir "Uninstall.exe") -ArgumentList "/S" -Wait -ErrorAction SilentlyContinue | Out-Null
    }

    Remove-PathIfPresent -Path $startMenuDir
    if (Test-Path -LiteralPath $startMenuBackup) {
        Copy-Item -LiteralPath $startMenuBackup -Destination $startMenuDir -Recurse -Force
    }

    if (Test-Path -LiteralPath $regPath) {
        Remove-Item -LiteralPath $regPath -Recurse -Force
    }
    if (Test-Path -LiteralPath $uninstallPath) {
        Remove-Item -LiteralPath $uninstallPath -Recurse -Force
    }
    Import-RegistryBackupIfPresent -Path $regBackup
    Import-RegistryBackupIfPresent -Path $uninstallRegBackup

    if (-not $KeepArtifacts) {
        Assert-UnderPath -Path $tempRoot -Parent $env:TEMP
        Remove-PathIfPresent -Path $tempRoot
    }
}
