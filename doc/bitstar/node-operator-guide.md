# BitStar Node Operator Guide

This guide is for running a BitStar Core node during bootstrap testing and later
public launch preparation.

## Status

BitStar Core is pre-release software. The current bootstrap binaries are for
local validation only. Do not rely on them for custody, merchant payments,
exchange deposits, or public mining.

## Configuration File

BitStar uses `bitstar.conf`.

Data directory locations:

- Windows: `%LOCALAPPDATA%\BitStar`
- macOS: `~/Library/Application Support/BitStar`
- Linux: `~/.bitstar`

Example local testing configuration:

```ini
server=1
rpcuser=bitstar
rpcpassword=change-this-password
listen=1
dnsseed=0
```

For public operation, use a strong RPC password and never expose RPC to the
public internet.

## Start A Local Node

From the folder containing the Windows bootstrap binaries:

```cmd
bitstard.exe -server=1 -rpcuser=bitstar -rpcpassword=localtest
```

To start isolated with no outbound peers:

```cmd
bitstard.exe -noconnect -dnsseed=0 -listen=0 -server=1 -rpcuser=bitstar -rpcpassword=localtest
```

## Verify The Chain

In another Command Prompt:

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest getblockhash 0
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest getblockchaininfo
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest getnetworkinfo
```

Expected genesis hash:

```text
00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49
```

Expected mainnet ports:

- P2P: `21333`
- RPC: `21332`

## Connect Two Local Nodes

Use separate data directories and ports:

Node 1:

```cmd
bitstard.exe -server=1 -rpcuser=bitstar -rpcpassword=localtest
```

Node 2:

```cmd
bitstard.exe -datadir=node2data -port=21402 -rpcport=21412 -connect=127.0.0.1:21333 -server=1 -rpcuser=bitstar -rpcpassword=localtest
```

Check peer count:

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest getconnectioncount
bitstar-cli.exe -datadir=node2data -rpcport=21412 -rpcuser=bitstar -rpcpassword=localtest getconnectioncount
```

## Stop Cleanly

```cmd
bitstar-cli.exe -rpcuser=bitstar -rpcpassword=localtest stop
bitstar-cli.exe -datadir=node2data -rpcport=21412 -rpcuser=bitstar -rpcpassword=localtest stop
```

## Public Node Checklist

- Use a dedicated VPS or server.
- Open P2P port `21333`.
- Do not expose RPC port `21332`.
- Use a strong RPC password.
- Monitor height, peers, disk, memory, and process health.
- Keep backups of wallet files only if wallet functionality is used.
- Do not reuse private test-chain data for a no-premine public launch.
