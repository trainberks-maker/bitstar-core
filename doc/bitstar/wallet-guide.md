# BitStar Wallet Safety Guide

BitStar Core includes wallet functionality when built with wallet support.

## Status

This is pre-release software. Do not store meaningful funds in bootstrap
wallets. Do not use bootstrap wallets for exchange deposits, merchant payments,
or custody.

## Create A Wallet

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest createwallet mywallet
```

Load an existing wallet:

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest loadwallet mywallet
```

Get a receiving address:

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest -rpcwallet=mywallet getnewaddress "" bech32
```

## Check Balances

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest -rpcwallet=mywallet getbalances
```

Common balance fields:

- `trusted`: confirmed and spendable balance
- `untrusted_pending`: pending incoming transactions
- `immature`: mined coinbase rewards that are not yet spendable

## Backup

Back up wallet files before deleting data directories or moving machines.

Windows wallet path:

```text
%LOCALAPPDATA%\BitStar\wallets
```

Do not share wallet files, private keys, seed phrases, or RPC credentials.

## Security Rules

- Use a strong local machine password.
- Keep backups offline.
- Do not expose RPC to the public internet.
- Do not run public services and high-value wallets on the same machine.
- Treat test-chain coins as test data only.
- Recheck the genesis hash before trusting any node or explorer.

## Public Release Wallet Checklist

- Test backup and restore.
- Test rescan.
- Test wallet encryption and unlock flows.
- Test transaction propagation across multiple nodes.
- Document recovery steps.
- Publish signed binaries and checksums.
- Warn users that no exchange listing or market value is guaranteed.
