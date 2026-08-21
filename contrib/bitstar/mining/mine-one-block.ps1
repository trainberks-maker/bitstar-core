param(
  [Parameter(Mandatory = $true)]
  [string]$Address,

  [string]$CliPath = ".\bitstar-cli.exe",
  [int]$Blocks = 1,
  [int]$MaxTries = 50000000,
  [string]$RpcUser = "",
  [string]$RpcPassword = "",
  [string]$RpcWallet = ""
)

$ErrorActionPreference = "Stop"

if (-not $Address.StartsWith("bst1")) {
  throw "Refusing to mine: address must start with bst1"
}

if ($Blocks -lt 1) {
  throw "Refusing to mine: Blocks must be a positive integer"
}

if ($Blocks -gt 10 -and $env:BITSTAR_ALLOW_MULTI_BLOCK -ne "1") {
  throw "Refusing to mine more than 10 blocks without BITSTAR_ALLOW_MULTI_BLOCK=1"
}

if ($MaxTries -lt 1) {
  throw "Refusing to mine: MaxTries must be a positive integer"
}

$rpcArgs = @()
if ($RpcUser) {
  $rpcArgs += "-rpcuser=$RpcUser"
}
if ($RpcPassword) {
  $rpcArgs += "-rpcpassword=$RpcPassword"
}
if ($RpcWallet) {
  $rpcArgs += "-rpcwallet=$RpcWallet"
}

Write-Host "BitStar controlled mining"
Write-Host "Address: $Address"
Write-Host "Blocks:  $Blocks"

$heightBefore = & $CliPath @rpcArgs getblockcount
Write-Host "Height before: $heightBefore"

& $CliPath @rpcArgs generatetoaddress $Blocks $Address $MaxTries

$heightAfter = & $CliPath @rpcArgs getblockcount
Write-Host "Height after:  $heightAfter"
Write-Host "Done. Coinbase rewards mature after 100 confirmations."
