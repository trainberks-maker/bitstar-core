BitStar Core
============

BitStar Core is a Bitcoin Core based Proof-of-Work cryptocurrency node and
wallet project.

## Official Links

- Website: https://bitstarcoin.org
- Source: https://github.com/trainberks-maker/bitstar-core
- Bootstrap release: https://github.com/trainberks-maker/bitstar-core/releases/tag/v0.1.0-bootstrap

## Network Summary

- Name: BitStar
- Ticker: BST
- Max supply: 21,000,000 BST
- Consensus: SHA256d Proof-of-Work
- Target block time: 10 minutes
- Halving interval: 210,000 blocks
- Initial subsidy: 50 BST
- Premine: none
- Mainnet P2P port: 21333
- Mainnet RPC port: 21332
- Bech32 prefix: `bst`

## Current Status

This repository is an early bootstrap fork. Local validation has confirmed:

- custom genesis block creation and validation
- local mining
- reward maturity
- wallet-to-wallet transfer
- two-node local synchronization

The current local mined chain is test data only. For a public no-premine launch,
public seed nodes should start from genesis and block 1 should be mined publicly.

## Documentation

- [Project spec](doc/bitstar/project-spec.md)
- [Fair launch plan](doc/bitstar/fair-launch.md)
- [Local test report](doc/bitstar/local-test-report.md)
- [Windows build guide](doc/bitstar/build-windows.md)
- [Linux build guide](doc/bitstar/build-linux.md)
- [Node operator guide](doc/bitstar/node-operator-guide.md)
- [VPS seed node guide](doc/bitstar/vps-seed-node-guide.md)
- [Mining guide](doc/bitstar/mining-guide.md)
- [Wallet safety guide](doc/bitstar/wallet-guide.md)
- [Public launch roadmap](doc/bitstar/public-launch-roadmap.md)

The broader upstream Bitcoin Core developer documentation remains available in
the [doc](doc) directory.

## Upstream

BitStar Core is derived from Bitcoin Core. Bitcoin Core is an open-source
project released under the MIT license. This fork keeps the same license terms;
see [COPYING](COPYING).

## Warning

This is pre-release software. Do not use this build for public mining, merchant
payments, exchange listing, custody, or production funds until the public launch
process, review, release signing, and infrastructure are complete.
