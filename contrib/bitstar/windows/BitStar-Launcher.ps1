param(
    [ValidateSet("menu", "start", "status", "stop", "backup", "datadir", "gui", "config")]
    [string]$Action = "menu",

    [string]$DataDir = (Join-Path $env:LOCALAPPDATA "BitStar"),

    [string]$ReleaseDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ReleaseDir)) {
    $ReleaseDir = $PSScriptRoot
}

$Daemon = Join-Path $ReleaseDir "bitstard.exe"
$Cli = Join-Path $ReleaseDir "bitstar-cli.exe"
$Gui = Join-Path $ReleaseDir "bitstar.exe"
$ConfPath = Join-Path $DataDir "bitstar.conf"
$SeedNodes = @("seed1.bitstarcoin.org:21333", "seed2.bitstarcoin.org:21333")

function New-RpcPassword {
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $bytes = New-Object byte[] 24
        $rng.GetBytes($bytes)
        return ([Convert]::ToBase64String($bytes).TrimEnd("=") -replace "[+/]", "")
    }
    finally {
        $rng.Dispose()
    }
}

function Get-ConfigLines {
    if (Test-Path -LiteralPath $ConfPath) {
        return @(Get-Content -LiteralPath $ConfPath)
    }
    return @()
}

function Test-ConfigHasKey {
    param(
        [string[]]$Lines,
        [string]$Key
    )

    $pattern = "^\s*$([regex]::Escape($Key))\s*="
    return [bool]($Lines | Where-Object { $_ -match $pattern } | Select-Object -First 1)
}

function Ensure-Config {
    if (-not (Test-Path -LiteralPath $DataDir)) {
        New-Item -ItemType Directory -Path $DataDir | Out-Null
    }

    if (-not (Test-Path -LiteralPath $ConfPath)) {
        $createdAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
        $password = New-RpcPassword
        $content = @(
            "# BitStar Core local node config",
            "# Created by BitStar Launcher on $createdAt",
            "server=1",
            "listen=1",
            "dnsseed=1",
            "rpcbind=127.0.0.1",
            "rpcallowip=127.0.0.1",
            "rpcuser=bitstar",
            "rpcpassword=$password",
            "addnode=seed1.bitstarcoin.org:21333",
            "addnode=seed2.bitstarcoin.org:21333"
        )
        Set-Content -LiteralPath $ConfPath -Value $content -Encoding ASCII
        Write-Host "Created local config: $ConfPath"
        return
    }

    $lines = Get-ConfigLines
    $append = New-Object System.Collections.Generic.List[string]

    foreach ($entry in @(
        @{ Key = "server"; Line = "server=1" },
        @{ Key = "listen"; Line = "listen=1" },
        @{ Key = "dnsseed"; Line = "dnsseed=1" },
        @{ Key = "rpcbind"; Line = "rpcbind=127.0.0.1" },
        @{ Key = "rpcallowip"; Line = "rpcallowip=127.0.0.1" },
        @{ Key = "rpcuser"; Line = "rpcuser=bitstar" }
    )) {
        if (-not (Test-ConfigHasKey -Lines $lines -Key $entry.Key)) {
            $append.Add($entry.Line)
        }
    }

    if (-not (Test-ConfigHasKey -Lines $lines -Key "rpcpassword")) {
        $append.Add("rpcpassword=$(New-RpcPassword)")
    }

    foreach ($seed in $SeedNodes) {
        if (-not ($lines | Where-Object { $_.Trim() -eq "addnode=$seed" } | Select-Object -First 1)) {
            $append.Add("addnode=$seed")
        }
    }

    if ($append.Count -gt 0) {
        Add-Content -LiteralPath $ConfPath -Value @("", "# Added by BitStar Launcher") -Encoding ASCII
        Add-Content -LiteralPath $ConfPath -Value $append -Encoding ASCII
        Write-Host "Updated local config: $ConfPath"
    }
}

function Require-Cli {
    if (-not (Test-Path -LiteralPath $Cli)) {
        throw "Missing bitstar-cli.exe in $ReleaseDir"
    }
}

function Invoke-BitStarCli {
    param([string[]]$Arguments)

    Require-Cli
    & $Cli "-datadir=$DataDir" @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "bitstar-cli failed with exit code $LASTEXITCODE"
    }
}

function Test-RpcReady {
    try {
        Require-Cli
        & $Cli "-datadir=$DataDir" "getblockchaininfo" 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Start-BitStarNode {
    Ensure-Config

    if (Test-RpcReady) {
        Write-Host "BitStar node is already running."
        return
    }

    if (-not (Test-Path -LiteralPath $Daemon)) {
        throw "Missing bitstard.exe in $ReleaseDir"
    }

    Write-Host "Starting BitStar node..."
    Start-Process -FilePath $Daemon -ArgumentList @("-datadir=$DataDir") -WorkingDirectory $ReleaseDir -WindowStyle Hidden

    for ($attempt = 1; $attempt -le 30; $attempt++) {
        Start-Sleep -Seconds 2
        if (Test-RpcReady) {
            Write-Host "BitStar node is running."
            Show-BitStarStatus
            return
        }
    }

    Write-Warning "BitStar started, but RPC is not ready yet. Try Status again in a minute."
}

function Show-BitStarStatus {
    Ensure-Config

    if (-not (Test-RpcReady)) {
        Write-Warning "BitStar node is not responding yet. Start it first, or wait a minute."
        return
    }

    $chain = Invoke-BitStarCli -Arguments @("getblockchaininfo") | ConvertFrom-Json
    $peers = Invoke-BitStarCli -Arguments @("getconnectioncount")

    Write-Host ""
    Write-Host "BitStar status"
    Write-Host "--------------"
    Write-Host "Data dir: $DataDir"
    Write-Host "Blocks:   $($chain.blocks)"
    Write-Host "Headers:  $($chain.headers)"
    Write-Host "Best:     $($chain.bestblockhash)"
    Write-Host "IBD:      $($chain.initialblockdownload)"
    Write-Host "Peers:    $peers"

    if ($chain.warnings -and $chain.warnings.Count -gt 0) {
        Write-Host ""
        Write-Warning ($chain.warnings -join "; ")
    }
}

function Stop-BitStarNode {
    Ensure-Config
    Require-Cli

    if (-not (Test-RpcReady)) {
        Write-Warning "BitStar node is not running or RPC is not ready."
        return
    }

    Invoke-BitStarCli -Arguments @("stop") | Out-Host
}

function Backup-BitStarWallets {
    Ensure-Config

    if (-not (Test-RpcReady)) {
        Write-Warning "BitStar node is not responding. Start it before wallet backup."
        return
    }

    $wallets = @(Invoke-BitStarCli -Arguments @("listwallets") | ConvertFrom-Json)
    if ($wallets.Count -eq 0) {
        Write-Warning "No loaded wallets were found."
        return
    }

    $backupDir = Join-Path $DataDir ("wallet-backups\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
    New-Item -ItemType Directory -Path $backupDir | Out-Null

    foreach ($wallet in $wallets) {
        $safeName = if ([string]::IsNullOrWhiteSpace($wallet)) { "default" } else { $wallet -replace "[^A-Za-z0-9_.-]", "_" }
        $target = Join-Path $backupDir "$safeName.dat"

        if ([string]::IsNullOrWhiteSpace($wallet)) {
            Invoke-BitStarCli -Arguments @("backupwallet", $target) | Out-Host
        }
        else {
            & $Cli "-datadir=$DataDir" "-rpcwallet=$wallet" "backupwallet" $target | Out-Host
            if ($LASTEXITCODE -ne 0) {
                throw "bitstar-cli failed with exit code $LASTEXITCODE"
            }
        }
    }

    Write-Host "Wallet backup folder: $backupDir"
}

function Open-BitStarDataDir {
    Ensure-Config
    Start-Process -FilePath "explorer.exe" -ArgumentList $DataDir
}

function Open-BitStarGui {
    Ensure-Config

    if (-not (Test-Path -LiteralPath $Gui)) {
        throw "Missing bitstar.exe in $ReleaseDir"
    }

    Start-Process -FilePath $Gui -ArgumentList @("-datadir=$DataDir") -WorkingDirectory $ReleaseDir
}

function Show-Menu {
    while ($true) {
        Clear-Host
        Write-Host "BitStar Launcher"
        Write-Host "================"
        Write-Host "Data dir: $DataDir"
        Write-Host ""
        Write-Host "1. Start node"
        Write-Host "2. Show status"
        Write-Host "3. Open wallet/GUI"
        Write-Host "4. Backup loaded wallet"
        Write-Host "5. Open data folder"
        Write-Host "6. Stop node"
        Write-Host "7. Ensure config"
        Write-Host "0. Exit"
        Write-Host ""

        $choice = Read-Host "Choose"
        try {
            switch ($choice) {
                "1" { Start-BitStarNode }
                "2" { Show-BitStarStatus }
                "3" { Open-BitStarGui }
                "4" { Backup-BitStarWallets }
                "5" { Open-BitStarDataDir }
                "6" { Stop-BitStarNode }
                "7" { Ensure-Config }
                "0" { return }
                default { Write-Warning "Unknown option." }
            }
        }
        catch {
            Write-Warning $_.Exception.Message
        }

        Write-Host ""
        Read-Host "Press Enter to continue"
    }
}

switch ($Action) {
    "menu" { Show-Menu }
    "start" { Start-BitStarNode }
    "status" { Show-BitStarStatus }
    "stop" { Stop-BitStarNode }
    "backup" { Backup-BitStarWallets }
    "datadir" { Open-BitStarDataDir }
    "gui" { Open-BitStarGui }
    "config" { Ensure-Config }
}
