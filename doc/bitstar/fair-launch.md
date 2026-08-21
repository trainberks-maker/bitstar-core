# BitStar Fair Launch Plan

## Current Status

BitStar has a working local bootstrap chain. The local test chain reached height
`181`, mined rewards into wallet `miner`, transferred `10 BST` to wallet
`user1`, and synchronized across two local nodes.

Those blocks are private test data. They should not be treated as public mainnet
history unless explicitly disclosed.

The current public seed chain is separate from the old local test chain. As of
August 21, 2026, seed1 and seed2 are synchronized at height `5`. This public
chain is still classified as bootstrap/test until a final launch decision is
published.

## Recommended No-Premine Path

1. Keep the local height `181` chain as development/test data only.
2. Do not hardcode the privately mined block 1 hash into public release binaries.
3. Before launch, clean seed-node data directories so they start from genesis
   with no privately mined blocks.
4. Publish source code, binaries, checksums, launch time, ports, genesis hash,
   and mining instructions before public mining starts.
5. Let block 1 be mined publicly after the launch announcement.
6. Publish explorer and seed nodes only after confirming they follow the public
   chain.

## Launch Decision Options

### Option A: Continue The Current Bootstrap Chain

This avoids another reset, but it requires full disclosure that the first public
blocks were mined during bootstrap testing. The public announcement must include
the early block history, seed nodes, explorer state, and current best block.

### Option B: Final Fair-Launch Reset

This is the cleanest Bitcoin-style path. The current chain is treated as a
public test, seed nodes are reset once, signed release artifacts are published,
and block 1 is mined only after the public launch time.

Recommended choice: Option B, unless the community intentionally accepts the
current bootstrap history.

## Why This Matters

The project goal is no premine. If the private test chain were reused as public
history, the `miner` wallet would already hold early rewards. That would not
look like a fair Bitcoin-style launch unless it was disclosed and intentionally
accepted by the community.

## Pre-Launch Reset Checklist

- Stop all local `bitstard` nodes.
- Back up test wallets only if they are needed for records.
- Do not ship `%LOCALAPPDATA%\BitStar` test chain data.
- Do not point public seed nodes at the local height `181` chain.
- Rebuild clean public release binaries from source.
- Run a final fresh-node test from genesis.

## Public Announcement Data

- Name: BitStar
- Ticker: BST
- Max supply: `21,000,000 BST`
- Premine: none
- Genesis hash: `00000c45c905ce3e3beeb9eb534650276947373d3a2a15694b4624a89bce4b49`
- P2P port: `21333`
- RPC port: `21332`
- Bech32 HRP: `bst`
- Message magic: `ba570b51`
