# BitStar Stratum Solo Test Pool

This directory contains a minimal Stratum V1 server for early BitStar mining
compatibility tests. It is not a production pooled-mining platform.

The server works as a solo test pool:

- miners connect over Stratum on TCP `3333`
- the worker username must be a valid BitStar payout address
- the pool builds block templates through local `bitstar-cli`
- the default bootstrap share difficulty is `0.00010`
- if a miner finds a valid block, the coinbase output pays the miner address
- no pooled payout accounting, balances, vardiff, or custody is provided
- a local operator stats file tracks submitted, rejected, accepted, and
  block-candidate shares
- an optional local JSONL history file records periodic stats snapshots for
  operator review; it is not a payout ledger
- a dry-run ledger report ranks workers by accepted shares for review only; it
  does not credit balances, sign payout transactions, or broadcast payments
- the dry-run ledger is persisted locally by default in SQLite at
  `/var/lib/bitstar/pool-dry-run-ledger.sqlite3`
- a JSON mirror is also written at `/var/lib/bitstar/pool-dry-run-ledger.json`
  for simple operator/API reads

## Install On A Seed Or Pool VPS

Run these commands on the Ubuntu server that already has `bitstard` installed:

```bash
sudo install -o root -g root -m 0755 bitstar-stratum-pool.py /usr/local/bin/bitstar-stratum-pool.py
sudo install -o root -g root -m 0644 bitstar-stratum-pool.service /etc/systemd/system/bitstar-stratum-pool.service
sudo systemctl daemon-reload
sudo systemctl enable --now bitstar-stratum-pool.service
```

Install the dry-run ledger backup helper and daily timer:

```bash
sudo install -o root -g root -m 0755 bitstar-pool-ledger-backup.py /usr/local/bin/bitstar-pool-ledger-backup.py
sudo install -o root -g root -m 0644 bitstar-pool-ledger-backup.service /etc/systemd/system/bitstar-pool-ledger-backup.service
sudo install -o root -g root -m 0644 bitstar-pool-ledger-backup.timer /etc/systemd/system/bitstar-pool-ledger-backup.timer
sudo install -d -o bitstar -g bitstar -m 0750 /var/backups/bitstar/pool
sudo systemctl daemon-reload
sudo systemctl enable --now bitstar-pool-ledger-backup.timer
```

If a firewall is active, allow the public Stratum port:

```bash
sudo ufw allow 3333/tcp
```

## Operator Status Checks

Follow live logs:

```bash
sudo journalctl -u bitstar-stratum-pool -f
```

Read the local stats snapshot:

```bash
sudo cat /var/lib/bitstar/pool-stats.json
```

Read the periodic stats history:

```bash
sudo tail -n 5 /var/lib/bitstar/pool-stats-history.jsonl
```

Read the persistent dry-run ledger:

```bash
sudo cat /var/lib/bitstar/pool-dry-run-ledger.json
```

Inspect the SQLite-backed dry-run ledger:

```bash
sudo -u bitstar /usr/local/bin/bitstar-pool-ledger-backup.py --json verify \
  /var/lib/bitstar/pool-dry-run-ledger.sqlite3
```

Create and verify a safe online backup:

```bash
sudo systemctl start bitstar-pool-ledger-backup.service
sudo journalctl -u bitstar-pool-ledger-backup -n 20 --no-pager
```

Run a restore drill without touching the live ledger:

```bash
sudo -u bitstar /usr/local/bin/bitstar-pool-ledger-backup.py --json restore-drill
sudo cat /var/lib/bitstar/pool-ledger-backup-status.json
```

Restore only during maintenance:

```bash
sudo systemctl stop bitstar-stratum-pool
sudo install -o bitstar -g bitstar -m 0640 /var/backups/bitstar/pool-dry-run-ledger-YYYYMMDDTHHMMSSZ.sqlite3 \
  /var/lib/bitstar/pool-dry-run-ledger.sqlite3
sudo systemctl start bitstar-stratum-pool
```

The restore-drill command copies a backup to a temporary database, opens it,
runs SQLite `quick_check`, verifies the dry-run ledger tables, and removes the
temporary copy by default. It does not overwrite the live pool database.

Important fields:

- `submitted_shares`: miner shares received by the pool
- `accepted_shares`: shares that met the pool share difficulty
- `rejected_low_difficulty`: shares below the configured pool share difficulty
- `candidate_blocks`: shares strong enough to be submitted as possible blocks
- `submitblock_success`: candidate blocks accepted by `bitstard`
- `accounting.mode`: currently `solo_direct_coinbase`
- `accounting.auto_payouts_enabled`: currently `false`
- `accounting.custody_enabled`: currently `false`
- `accounting.dry_run_ledger_enabled`: currently `true`
- `accounting.dry_run_ledger_persistent`: currently `true`
- `accounting.dry_run_ledger_storage`: currently `sqlite`
- `accounting.dry_run_ledger_database`: currently `true`
- `accounting.dry_run_ledger_backup_required`: currently `true`
- `dry_run_ledger`: review-only proportional share report; no payments are
  signed or broadcast

Miner output such as `Submitted Diff ...` only means the miner sent shares to
the Stratum server. It does not mean a BitStar block was mined unless the pool
stats show `candidate_blocks` and `submitblock_success`, and the public chain
height increases.

The public website may display a sanitized pool dashboard from these stats. The
dashboard is an operational signal only. It is not a balance ledger, payout
promise, exchange signal, or profit estimate.

## Check RPC Compatibility

```bash
sudo -u bitstar /usr/local/bin/bitstar-stratum-pool.py --check
```

Expected fields include:

- chain: `main`
- template height: current next block height
- coinbasevalue: `5000000000` at launch difficulty/subsidy
- bits: `1e0ffff0` at the bootstrap height

## Miner Configuration

Use the miner's BitStar address as the username. Password can be any value.

```text
stratum+tcp://pool.bitstarcoin.org:3333
username: bst1...your...address
password: x
algorithm: sha256d
```

Example cpuminer-style command:

```bash
cpuminer -a sha256d -o stratum+tcp://pool.bitstarcoin.org:3333 -u bst1... -p x
```

## Security Notes

- Keep BitStar RPC bound to `127.0.0.1`.
- Do not expose RPC port `21332` to the public internet.
- This pool does not custody miner funds.
- This pool does not promise rewards, profit, exchange listing, or production
  reliability.
- Treat this as a bootstrap compatibility tool until reviewed by operators and
  miners.
