# BitStar External Mining Pool Verification

Release cycle: `v0.1.2-rc3`

Date recorded: 2026-08-23

## Scope

This record captures an external Windows mining smoke test against the public
BitStar Stratum endpoint. It verifies that a non-maintainer Windows machine can
create or load a BitStar wallet, save a wallet backup, connect a CPU miner to
the public test pool, and receive accepted shares.

This is not a production payout-pool certification. The current public endpoint
is still a solo/test compatibility pool.

## Public Endpoint

```text
stratum+tcp://pool.bitstarcoin.org:3333
```

DNS and port status observed:

- `pool.bitstarcoin.org` resolved to `134.122.66.31`
- TCP `3333` was reachable from the tester network

## Tester Flow Observed

The external Windows tester:

1. Started the BitStar node from the Windows launcher package.
2. Confirmed the node could query chain height through `bitstar-cli`.
3. Created or loaded wallet `wallet1`.
4. Generated a `bst1` receive address.
5. Saved a wallet backup file.
6. Started `cpuminer` against `pool.bitstarcoin.org:3333`.
7. Observed repeated accepted shares.

Public payout/mining address used for the smoke test:

```text
bst1qpeqa3uqc9nfn28qr8tnhzkhph83fgph8srkx8k
```

Representative miner output observed:

```text
Accepted ... S0 R0 ...
Submitted Diff ... Block 8020 ...
```

The important signal is `Accepted`, which confirms the pool accepted shares
from the external miner. A share acceptance smoke test does not by itself prove
full production payout accounting.

## Result

| Check | Result |
| --- | --- |
| External Windows machine used | PASS |
| Wallet created or loaded | PASS |
| `bst1` address generated | PASS |
| Wallet backup created | PASS |
| Pool DNS reachable | PASS |
| Pool TCP `3333` reachable | PASS |
| Miner connected to public pool | PASS |
| Shares accepted by pool | PASS |
| Production payout pool certified | NOT CERTIFIED |

Overall external mining/pool smoke result: PASS.

## Limitations

- The pool remains a solo/test Stratum compatibility endpoint.
- There is no public miner dashboard yet.
- There is no production share ledger or automatic pooled payout system yet.
- Accepted shares do not represent a guaranteed payout balance.
- Coinbase rewards, if a valid block is found, are spendable only after normal
  maturity.
- The release remains a signed pre-release candidate, not a final production
  release.

## Follow-Up

- Keep collecting optional external miner reports from different networks and
  hardware.
- Keep the website and docs labeling the endpoint as solo/test.
- Do not advertise the endpoint as an official payout pool until the production
  pool gate is complete.
- Build and test the pool dashboard, share accounting, payout accounting,
  wallet isolation, backup/restore drill, and public terms before any future
  pooled payout launch.
