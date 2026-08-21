# BitStar Local Test Report

Date: 2026-08-21

## Build Under Test

- Package: `BitStar_Bootstrap_Windows`
- Binaries: `bitstard.exe`, `bitstar-cli.exe`, `bitstar-util.exe`, `bitstar.exe`
- Runtime dependency: `sqlite3.dll`
- Network: BitStar main chain parameters, local/private nodes only

## Chain Parameters Verified

- Genesis hash: `00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49`
- Block target spacing: `600` seconds
- Main P2P port: `21333`
- Main RPC port: `21332`
- Message magic: `ba570b51`
- Bech32 HRP: `bst`
- P2P subversion: `/BitStar:31.99.0/`

## Mining Validation

- Block 1 hash: `00000118d75fb3f4a423a2e2e01c5d2ca4cd9341313cbf01910ae529e6f6535f`
- Height after reward-maturity mining: `179`
- Height after transfer-confirmation mining: `180`
- Height after two-node sync mining: `181`

## Wallet Validation

- Miner wallet: `miner`
- User wallet: `user1`
- Mining address used: `bst1q8x4dnwudeq4ke6zkq69we23gx8wdk0rase0hl7`
- User receive address: `bst1q9dwqqp6vsa2lu6ahvggnkscv44dk2djmn8t7tt`
- Miner balance at height `179`: `trusted=3950.00000000`,
  `immature=5000.00000000`
- Transfer amount: `10 BST`
- Transfer txid: `b9249ec1d11bf263fb1493ac2c25789c0c35a853c1a5596ecbc6391bf81d2c5b`
- User wallet balance after confirmation: `trusted=10.00000000`

## Multi-Node Sync Validation

- Node 1: default data directory, P2P `127.0.0.1:21333`, RPC `21332`
- Node 2: `node2data`, P2P `127.0.0.1:21402`, RPC `21412`
- Node 1 connection count: `1`
- Node 2 connection count: `1`
- Node 2 synchronized to height `180`
- Node 1 mined block `181`
- Node 2 observed and advanced to height `181`

## Result

The BitStar bootstrap passed local validation for genesis, mining, wallet
rewards, reward maturity, wallet-to-wallet transfer, transaction confirmation,
and two-node sync.

This is still a local bootstrap build. It is not ready for public mining,
public funds, merchant use, exchange listing, or broker submission.
