# BitStar Public Mining Guide

BitStar is a Bitcoin Core based proof-of-work network with no premine. Mining
must be public, repeatable, and easy to audit. This guide documents the launch
rules and the commands miners can use to connect to the public seed nodes.

## Network Parameters

- Name: BitStar
- Ticker: BST
- Maximum supply: 21,000,000 BST
- Consensus: SHA256d proof of work
- Target block time: 10 minutes
- Halving interval: 210,000 blocks
- Coinbase maturity: 100 confirmations
- P2P port: 21333
- Bech32 prefix: `bst1`
- Genesis hash:
  `00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49`

## Public Seed Nodes

Use the public seed nodes below when joining the BitStar network:

```text
seed1.bitstarcoin.org:21333
seed2.bitstarcoin.org:21333
```

RPC is private to each node and must not be exposed to the public internet.

## Current Public Chain State

As of August 21, 2026, the public bootstrap chain is synchronized on seed1 and
seed2 at height `5`.

- Height: 5
- Current best block:
  `00000e7ed0c7df4e0db2d66c8d0031042e1ad66f5a8e3bf3e23a8e6a151c502d`
- Block 1 reward address:
  `bst1q8x4dnwudeq4ke6zkq69we23gx8wdk0rase0hl7`

The block reward follows normal proof-of-work coinbase rules and matures after
100 confirmations. There is no special allocation or hidden premine wallet.

## Fair Launch Rule

Do not run hidden nonstop mining before public launch coordination. Every mined
block should be visible on the public network and explorer. A private balance
created before public miners can join will look like a premine and will hurt
listing, exchange, and community credibility.

Recommended policy:

- publish source code, binaries, checksums, seeds, and explorer first
- announce mining instructions publicly before sustained mining
- mine controlled blocks only when needed for testing or confirmation
- document any early block rewards transparently
- never make price, profit, or listing guarantees

## Start A Node

Create or edit `bitstar.conf` on your node and add:

```ini
server=1
listen=1
port=21333
dnsseed=0
addnode=seed1.bitstarcoin.org:21333
addnode=seed2.bitstarcoin.org:21333
```

On Windows, from the BitStar release folder:

```cmd
bitstard.exe -server=1 -listen=1 -addnode=seed1.bitstarcoin.org:21333 -addnode=seed2.bitstarcoin.org:21333
```

Check chain and peer status:

```cmd
bitstar-cli.exe getblockchaininfo
bitstar-cli.exe getconnectioncount
```

## Create Or Load A Mining Wallet

Wallet commands are only available on wallet-enabled builds. If your node build
does not include wallet support, generate the receiving address on another
wallet-enabled BitStar node and mine to that address.

Create a mining wallet:

```cmd
bitstar-cli.exe createwallet miner
```

If the wallet already exists:

```cmd
bitstar-cli.exe loadwallet miner
```

Generate a receiving address:

```cmd
bitstar-cli.exe -rpcwallet=miner getnewaddress "" bech32
```

BitStar bech32 addresses begin with `bst1`.

## Mine One Controlled Block

Replace the address with your own `bst1...` address:

```cmd
bitstar-cli.exe generatetoaddress 1 bst1... 50000000
```

Confirm the new height:

```cmd
bitstar-cli.exe getblockcount
```

Check wallet balances:

```cmd
bitstar-cli.exe -rpcwallet=miner getbalances
```

New coinbase rewards appear as immature until 100 confirmations.

## Helper Scripts

Controlled one-block helper scripts are provided in:

```text
contrib/bitstar/mining/mine-one-block.sh
contrib/bitstar/mining/mine-one-block.ps1
```

Linux example:

```bash
BITSTAR_MINING_ADDRESS=bst1... ./contrib/bitstar/mining/mine-one-block.sh
```

Windows PowerShell example:

```powershell
.\contrib\bitstar\mining\mine-one-block.ps1 -Address "bst1..."
```

The scripts default to one block and refuse larger runs unless explicitly
overridden. This is intentional: public mining should be coordinated, visible,
and auditable.

## Public Explorer

Use the explorer to verify chain height, latest blocks, and seed status:

```text
https://bitstarcoin.org/explorer
```

## Public Mining Checklist

Before asking the public to mine, BitStar should have:

- public source code
- public release binaries and checksums
- at least two stable seed nodes
- public DNS records for seed nodes
- block explorer
- documented genesis hash and current best block
- published mining instructions
- documented no-premine statement
- security, legal, and listing readiness review
