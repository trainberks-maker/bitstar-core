param(
    [ValidateSet("menu", "start", "status", "stop", "backup", "datadir", "gui", "wallet", "config")]
    [string]$Action = "menu",

    [string]$DataDir = (Join-Path $env:LOCALAPPDATA "BitStar"),

    [string]$ReleaseDir = "",

    [string]$WalletName = "wallet1"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ReleaseDir)) {
    $ReleaseDir = $PSScriptRoot
}

$Daemon = Join-Path $ReleaseDir "bitstard.exe"
$Cli = Join-Path $ReleaseDir "bitstar-cli.exe"
$Gui = Join-Path $ReleaseDir "bitstar.exe"
$QtGui = Join-Path $ReleaseDir "bitstar-qt.exe"
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

function Invoke-BitStarCliCapture {
    param([string[]]$Arguments)

    Require-Cli
    $raw = @(& $Cli "-datadir=$DataDir" @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    $lines = @($raw | ForEach-Object { $_.ToString() })
    $newline = [Environment]::NewLine
    $text = $lines -join $newline

    [pscustomobject]@{
        ExitCode = $exitCode
        Text = $text
        Lines = $lines
    }
}

function Get-LoadedBitStarWallets {
    $result = Invoke-BitStarCliCapture -Arguments @("listwallets")
    if ($result.ExitCode -ne 0) {
        throw "Could not list loaded wallets. $($result.Text)"
    }

    if ([string]::IsNullOrWhiteSpace($result.Text)) {
        return @()
    }

    return @($result.Text | ConvertFrom-Json)
}

function Test-BitStarWalletExists {
    $walletDirResult = Invoke-BitStarCliCapture -Arguments @("listwalletdir")
    if ($walletDirResult.ExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($walletDirResult.Text)) {
        try {
            $walletDir = $walletDirResult.Text | ConvertFrom-Json
            foreach ($wallet in @($walletDir.wallets)) {
                $name = [string]$wallet.name
                if ($name -eq $WalletName -or (Split-Path -Leaf $name) -eq $WalletName) {
                    return $true
                }
            }
        }
        catch {
            Write-Verbose "Could not parse listwalletdir output: $($_.Exception.Message)"
        }
    }

    $walletPaths = @(
        (Join-Path (Join-Path $DataDir "wallets") $WalletName),
        (Join-Path $DataDir $WalletName)
    )

    foreach ($path in $walletPaths) {
        if (Test-Path -LiteralPath $path) {
            return $true
        }
    }

    return $false
}

function Ensure-BitStarWalletLoaded {
    $loadedWallets = @(Get-LoadedBitStarWallets)
    if ($loadedWallets -contains $WalletName) {
        return
    }

    $load = Invoke-BitStarCliCapture -Arguments @("loadwallet", $WalletName)
    if ($load.ExitCode -eq 0 -or $load.Text -match "already loaded") {
        return
    }

    if (Test-BitStarWalletExists) {
        throw "Wallet '$WalletName' exists but could not be loaded. The launcher will not overwrite it. Details: $($load.Text)"
    }

    $create = Invoke-BitStarCliCapture -Arguments @("createwallet", $WalletName)
    if ($create.ExitCode -eq 0) {
        return
    }

    if ($create.Text -match "already exists|Database already exists") {
        $retry = Invoke-BitStarCliCapture -Arguments @("loadwallet", $WalletName)
        if ($retry.ExitCode -eq 0 -or $retry.Text -match "already loaded") {
            return
        }

        throw "Wallet '$WalletName' exists but could not be loaded. The launcher will not overwrite it. Details: $($retry.Text)"
    }

    throw "Could not load or create wallet '$WalletName'. Details: $($create.Text)"
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

    $wallets = @(Get-LoadedBitStarWallets)
    if ($wallets.Count -eq 0) {
        try {
            Ensure-BitStarWalletLoaded
            $wallets = @(Get-LoadedBitStarWallets)
        }
        catch {
            Write-Warning $_.Exception.Message
            return
        }
    }

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

function Get-OrCreate-BitStarWalletAddress {
    Ensure-Config

    if (-not (Test-RpcReady)) {
        Write-Host "BitStar node is not running yet. Starting it now..."
        Start-BitStarNode
    }

    if (-not (Test-RpcReady)) {
        Write-Warning "BitStar node is not responding yet. Wait a minute, then try wallet address again."
        return
    }

    Ensure-BitStarWalletLoaded

    $address = & $Cli "-datadir=$DataDir" "-rpcwallet=$WalletName" "getnewaddress" "" "bech32"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create a receiving address for wallet '$WalletName'."
    }

    $desktop = [Environment]::GetFolderPath("Desktop")
    if ([string]::IsNullOrWhiteSpace($desktop)) {
        $desktop = Join-Path $env:USERPROFILE "Desktop"
    }

    $addressFile = Join-Path $desktop "bitstar-address.txt"
    $addressRecord = @(
        "# BitStar mining address",
        "wallet=$WalletName",
        "address=$address",
        "pool=pool.bitstarcoin.org:3333"
    )
    Set-Content -LiteralPath $addressFile -Value $addressRecord -Encoding ASCII

    Write-Host ""
    Write-Host "BitStar wallet address"
    Write-Host "----------------------"
    Write-Host "Wallet:  $WalletName"
    Write-Host "Address: $address"
    Write-Host "Saved:   $addressFile"
    Write-Host ""
    Write-Host "Use this address for mining:"
    Write-Host ".\cpuminer-avx2.exe -a sha256d -o stratum+tcp://pool.bitstarcoin.org:3333 -u $address -p x -t 2"
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

    if (-not (Test-Path -LiteralPath $QtGui)) {
        Write-Warning "This package does not include bitstar-qt.exe, so the graphical wallet cannot open."
        Write-Host "Use option 3 to create/load wallet '$WalletName' and print a mining address."
        return
    }

    Start-Process -FilePath $Gui -ArgumentList @("gui", "-datadir=$DataDir") -WorkingDirectory $ReleaseDir
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
        Write-Host "3. Create/load wallet + show/save address"
        Write-Host "4. Backup loaded wallet"
        Write-Host "5. Open wallet/GUI if included"
        Write-Host "6. Open data folder"
        Write-Host "7. Stop node"
        Write-Host "8. Ensure config"
        Write-Host "0. Exit"
        Write-Host ""

        $choice = Read-Host "Choose"
        try {
            switch ($choice) {
                "1" { Start-BitStarNode }
                "2" { Show-BitStarStatus }
                "3" { Get-OrCreate-BitStarWalletAddress }
                "4" { Backup-BitStarWallets }
                "5" { Open-BitStarGui }
                "6" { Open-BitStarDataDir }
                "7" { Stop-BitStarNode }
                "8" { Ensure-Config }
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
    "wallet" { Get-OrCreate-BitStarWalletAddress }
    "config" { Ensure-Config }
}
