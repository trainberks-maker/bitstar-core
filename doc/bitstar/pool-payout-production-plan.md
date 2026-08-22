# BitStar Pool Payout Production Plan

This document defines the minimum plan before BitStar enables any production
pooled payout system. It is intentionally conservative: the current public pool
remains a solo/direct-coinbase compatibility pool until these gates are met.

## Current Status

The official public endpoint is still `solo_direct_coinbase`:

- miners use a valid `bst1` address as the Stratum username
- candidate block coinbase outputs pay that address directly
- the pool does not custody balances
- the pool does not credit live pooled balances
- the pool does not sign or broadcast payout transactions
- the SQLite dry-run ledger is for review, not for payment

This means the public pool can test mining compatibility without becoming a
custodial accounting system.

## Production Payout Gate

Automatic or operator-assisted pooled payouts must stay disabled until all of
these are complete:

- durable database schema for rounds, shares, workers, rewards, payout batches,
  payout outputs, and audit events
- coinbase maturity enforcement for every accepted block before any reward is
  considered payable
- reorg handling that reverses or quarantines affected rewards
- dry-run payout reports that reconcile with chain data for at least one full
  test window
- online backups and restore drills for the payout database
- signed release binaries and documented upgrade procedure for pool operators
- independent review of payout accounting and wallet signing code
- documented operator runbook for pause, resume, rollback, and incident review

## Recommended Reward Mode

Phase 0 remains solo/direct coinbase. No pooled balances.

Phase 1, if BitStar opens a production public pool, should use a round-based
proportional payout model:

- a round starts after one accepted pool block or at pool service start
- valid accepted shares are counted per worker during the round
- a matured block reward is split by each worker's share weight in that round
- payout reports are generated first in dry-run mode
- payout batches require operator review before signing

This model is easier to audit than PPS during the bootstrap phase because it
does not require the operator to assume long-term variance risk.

PPLNS can be evaluated later after the pool has stable hashrate history and
more public miner participation.

## Required Database Model

A production payout database should track at least:

- `workers`: worker identifier, payout address, first seen, last seen, status
- `rounds`: start height/time, end height/time, pool block hash, status
- `shares`: round id, worker id, accepted share count, share difficulty sum
- `candidate_blocks`: submitted block hash, height, worker, submit result
- `matured_rewards`: block hash, height, reward amount, maturity status
- `payout_batches`: created time, status, total amount, fee, signed txid
- `payout_outputs`: batch id, worker id, address, amount, status
- `audit_events`: operator action, timestamp, reason, before/after state
- `reorg_events`: old block, new block, affected round/reward status

SQLite is acceptable for the first reviewed operator deployment only if backups,
restore drills, WAL handling, and single-writer operation are documented. A
larger public pool should move to a managed database with tested snapshots and
restricted credentials.

## Payout State Machine

Every production reward should move through explicit states:

1. `candidate_submitted`: a pool share was submitted as a block candidate
2. `block_accepted`: the node accepted the candidate block
3. `immature`: the block is on chain but has fewer than 100 confirmations
4. `matured`: the block has at least 100 confirmations and no reorg conflict
5. `dry_run_calculated`: the payout split was calculated without signing
6. `reviewed`: the operator approved the payout batch
7. `signed`: a transaction was signed by the payout wallet
8. `broadcast`: the transaction was broadcast to the BitStar network
9. `confirmed`: the payout transaction confirmed on chain
10. `reconciled`: chain data, database totals, and wallet records match

No state may skip maturity, dry-run calculation, or reconciliation.

## Initial Policy Values

These are proposed bootstrap values, not active payout rules:

- coinbase maturity: 100 confirmations
- minimum payout threshold: operator-configured, with `1 BST` as an initial
  review candidate
- payout cadence: manual review first, then daily only after stable operation
- transaction fee policy: explicit configured fee, never hidden from reports
- dust handling: do not create outputs below the node's relay policy
- wallet exposure: use a payout wallet with limited balance, not treasury funds

## Operator Controls

Production payout software must support:

- global payout pause
- worker payout quarantine
- batch cancellation before broadcast
- re-run dry-run calculation by block height range
- export of payout batch JSON before signing
- restore from backup into a separate verification database
- read-only public status that never exposes private paths, RPC credentials, or
  wallet internals

## Public Communication Rules

Before announcing pooled payouts, public pages must state:

- whether the pool is solo/direct coinbase or pooled payout mode
- whether balances are live or dry-run only
- coinbase maturity requirement
- minimum payout threshold and cadence
- that mining rewards are probabilistic and never guaranteed
- that exchange, broker, liquidity, price, or profit outcomes are not guaranteed

## Test Checklist

Before enabling payouts:

- run unit tests for share weighting, rounding, dust handling, and fee handling
- run integration tests against a private BitStar node
- mine test rounds with multiple workers
- simulate block maturity and one reorg
- run a backup and restore drill of the payout database
- compare dry-run payout totals with expected round rewards
- create a signed-but-not-broadcast transaction in an isolated test wallet
- complete an operator review using exported batch JSON

## Launch Decision

The first public production move should not be "turn on automatic payouts".
It should be:

1. keep solo/direct-coinbase public mining live
2. publish dry-run payout reports for transparency
3. run a fixed test window with public miners
4. review and reconcile reports against chain data
5. only then decide whether a production pooled payout wallet is justified

Until then, BitStar's official pool status is: compatibility/test pool with
verified dry-run accounting, not a custodial payout pool.
