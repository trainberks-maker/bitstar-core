# BitStar Launch And Mining Announcement

Published: August 21, 2026

BitStar is opening its public bootstrap mining instructions for miners, node
operators, and pool operators who want to test and validate the network.

## Summary

- Name: BitStar
- Ticker: BST
- Consensus: SHA256d proof of work
- Maximum supply: 21,000,000 BST
- Target block time: 10 minutes
- Halving interval: 210,000 blocks
- Premine: none
- P2P port: 21333
- Explorer: https://bitstarcoin.org/explorer
- Website: https://bitstarcoin.org
- Source: https://github.com/trainberks-maker/bitstar-core

## Fair Launch Statement

BitStar has no premine and no hidden founder allocation. Early mining history
must stay public, auditable, and visible on the explorer. The project will not
run private nonstop mining to accumulate an undisclosed balance before public
participants can join.

The public bootstrap chain currently contains one mined block after genesis:

- Genesis:
  `00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49`
- Block 1:
  `00000738ca472e32ea8a6a247de802b4b2b031af610057a0c5158b12fb31b3d4`
- Block 1 reward address:
  `bst1q8x4dnwudeq4ke6zkq69we23gx8wdk0rase0hl7`

Block rewards follow Bitcoin-style coinbase maturity and mature after 100
confirmations.

## How To Join

Run a BitStar node and connect to the public seed nodes:

```text
seed1.bitstarcoin.org:21333
seed2.bitstarcoin.org:21333
```

Windows example:

```cmd
bitstard.exe -server=1 -listen=1 -addnode=seed1.bitstarcoin.org:21333 -addnode=seed2.bitstarcoin.org:21333
```

Verify the chain:

```cmd
bitstar-cli.exe getblockchaininfo
bitstar-cli.exe getconnectioncount
```

Generate a mining address on a wallet-enabled build:

```cmd
bitstar-cli.exe createwallet miner
bitstar-cli.exe -rpcwallet=miner getnewaddress "" bech32
```

Mine a controlled block:

```cmd
bitstar-cli.exe generatetoaddress 1 bst1... 50000000
```

## Pool Operators

BitStar exposes Bitcoin-style mining RPC on private local nodes. Pool operators
should run their own full node and connect it to the public seed nodes. Use
`getblocktemplate '{"rules":["segwit"]}'` and submit candidate blocks with
`submitblock`.

Pool compatibility details are documented in:

```text
doc/bitstar/mining-pool-compatibility.md
```

## Warnings

BitStar is still pre-release software. Mining rewards are not investment
guarantees. Do not use bootstrap builds for custody, merchant payments, exchange
deposits, or production funds until the project has completed release signing,
security review, legal review, and broader public validation.

No exchange, broker, price, liquidity, or profit outcome is guaranteed.
