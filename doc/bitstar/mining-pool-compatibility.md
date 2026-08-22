# BitStar Mining Pool Compatibility

This document gives mining pool operators the baseline information needed to
test BitStar. It is a compatibility note, not a certification that any pool
software is production-ready for BitStar.

## Status

As of the public bootstrap launch:

- public seed nodes are online
- P2P port `21333` is reachable on seed1 and seed2
- RPC remains private and bound to localhost on seed nodes
- `getmininginfo` is available on seed1 and seed2
- `getblocktemplate` is available on seed1 and seed2 with segwit rules
- the public Stratum test endpoint is open at `pool.bitstarcoin.org:3333`
- live chain height should be verified on `https://bitstarcoin.org/explorer`
- live sanitized pool stats are published through the explorer API when the pool
  stats file is available

The bootstrap build still prints a pre-release warning. Do not use it for
custody, merchant payments, exchange deposits, or guaranteed production mining.

## Network Values

| Field | Value |
| --- | --- |
| Name | BitStar |
| Ticker | BST |
| Algorithm | SHA256d |
| Target block time | 10 minutes |
| Coinbase maturity | 100 confirmations |
| Initial subsidy | 50 BST |
| P2P port | 21333 |
| RPC port | 21332 |
| Bech32 prefix | `bst1` |
| Genesis hash | `00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49` |
| Current best block | `00000e7ed0c7df4e0db2d66c8d0031042e1ad66f5a8e3bf3e23a8e6a151c502d` |

## Public Peers

Pool operators should run their own BitStar full node and connect it to:

```text
seed1.bitstarcoin.org:21333
seed2.bitstarcoin.org:21333
```

Never point mining pool software at public seed RPC. Seed RPC is intentionally
private. Pools should use their own local node RPC, usually on
`127.0.0.1:21332`.

## Required RPC Methods

The pool node should support at least:

```text
getblockchaininfo
getnetworkinfo
getmininginfo
getblocktemplate
submitblock
validateaddress
```

Wallet RPC may be needed for pool payout testing if the pool manages payouts
through the node wallet. Pool software that manages payouts externally should
still validate BitStar addresses beginning with `bst1`.

## getmininginfo Baseline

Verified on seed1 and seed2 on August 21, 2026:

```json
{
  "blocks": 5,
  "bits": "1e0ffff0",
  "difficulty": 0.000244140625,
  "target": "00000ffff0000000000000000000000000000000000000000000000000000000",
  "chain": "main",
  "next": {
    "height": 6,
    "bits": "1e0ffff0",
    "difficulty": 0.000244140625,
    "target": "00000ffff0000000000000000000000000000000000000000000000000000000"
  }
}
```

## getblocktemplate Baseline

Verified command:

```bash
bitstar-cli -datadir=/var/lib/bitstar -conf=/etc/bitstar/bitstar.conf \
  getblocktemplate '{"rules":["segwit"]}'
```

Important template fields observed on seed1 and seed2 on August 21, 2026:

```json
{
  "capabilities": ["proposal"],
  "version": 536870912,
  "rules": ["csv", "!segwit", "taproot"],
  "previousblockhash": "00000e7ed0c7df4e0db2d66c8d0031042e1ad66f5a8e3bf3e23a8e6a151c502d",
  "coinbasevalue": 5000000000,
  "target": "00000ffff0000000000000000000000000000000000000000000000000000000",
  "bits": "1e0ffff0",
  "height": 6,
  "weightlimit": 4000000
}
```

`coinbasevalue` is denominated in satoshi-style base units. `5000000000`
represents 50 BST.

## Pool Configuration Checklist

- Use algorithm `sha256d`.
- Use your own full node RPC on `127.0.0.1:21332`.
- Connect your node to both public seed nodes.
- Confirm `getblockcount` matches the public explorer.
- Confirm `getblocktemplate '{"rules":["segwit"]}'` returns height `2` or the
  current next height.
- Use a payout address beginning with `bst1`.
- Treat coinbase rewards as spendable only after 100 confirmations.
- Keep RPC credentials private.
- Do not expose RPC port `21332` to the public internet.
- Do not mine hidden private blocks before public launch coordination.

## Public Test Stratum Endpoint

A minimal solo-style Stratum test pool is provided in:

```text
contrib/bitstar/pool/
```

The public test endpoint is active:

```text
stratum+tcp://pool.bitstarcoin.org:3333
```

`pool.bitstarcoin.org` resolves to seed2 at `134.122.66.31`. This endpoint is
for compatibility testing only. Miners should use a valid BitStar address as the
worker username. If a valid block is found, the coinbase reward is paid directly
to that address after normal coinbase maturity. The test pool does not custody
miner balances and does not implement automatic pooled payouts.

## Production Pool Baseline

The current official endpoint runs in `solo_direct_coinbase` mode:

- miners use a valid `bst1` address as the Stratum username
- candidate block coinbase outputs pay that address directly
- coinbase rewards become spendable only after 100 confirmations
- the pool writes a local JSON stats snapshot for operators
- the pool can append periodic JSONL history snapshots for review
- the public API exposes sanitized counters and accounting flags only

The current baseline intentionally keeps these disabled:

- custodial miner balances
- automatic pooled payouts
- payout-address changes managed by the pool
- exchange, broker, liquidity, or profit guarantees

Before BitStar enables a real pooled payout system, operators should complete:

- a documented reward method such as solo, PPS, PPLNS, or proportional
- a durable database-backed share and payout ledger
- coinbase maturity handling before payouts are released
- minimum payout rules, dust handling, and fee policy
- dry-run payout reports before any live transaction is broadcast
- signed release builds for pool and node binaries
- monitoring, backups, and restore drills
- independent review of payout code and operational controls

## Compatibility Test Flow

1. Install BitStar Core on a pool test server.
2. Configure the node with both public seed nodes.
3. Wait for the node to sync with the public chain.
4. Confirm `getnetworkinfo`, `getblockchaininfo`, and `getmininginfo`.
5. Confirm `getblocktemplate '{"rules":["segwit"]}'`.
6. Configure pool software for SHA256d and the local BitStar RPC.
7. Test address validation for `bst1` payout addresses.
8. Test a controlled low-volume mining run only after public coordination.
9. Verify any mined block on `https://bitstarcoin.org/explorer`.

## Current Limitations

- The official endpoint is a public solo-style test pool, not a full payout pool.
- Release signing exists as a workflow, but reproducible release verification is
  still pending.
- DNS seed infrastructure is not active; documented static seed nodes are used.
- The bootstrap build still carries a pre-release warning.
- Pool dashboard counters are operational status signals, not balances.
- Exchange listing, liquidity, and market support are not guaranteed.

Report compatibility issues through the public GitHub issue tracker.
