# BitStar Operator Runbook

This runbook is the day-to-day operating procedure for BitStar public
bootstrap infrastructure: seed nodes, explorer API, and the solo/test Stratum
pool.

Current status: public bootstrap / early public test. Do not use this runbook
as proof that BitStar is production-ready. It is the operating checklist that
helps the project move toward that state safely.

## Scope

Covered infrastructure:

- `seed1.bitstarcoin.org:21333`
- `seed2.bitstarcoin.org:21333`
- `pool.bitstarcoin.org:3333`
- `https://bitstarcoin.org/explorer`
- `https://bitstarcoin.org/pool`

Important ports:

| Purpose | Port | Public |
| --- | ---: | --- |
| P2P | `21333/tcp` | yes |
| RPC | `21332/tcp` | no, localhost only |
| ZMQ/internal | `21334/tcp` | no, localhost only |
| Stratum test pool | `3333/tcp` | yes while advertised |
| Explorer API | `8090/tcp` | yes until reverse proxy is added |

## Non-Negotiable Safety Rules

- Never expose RPC port `21332` to the public internet.
- Never publish RPC usernames, RPC passwords, SSH private keys, wallet files,
  deployment tokens, or release signing private keys.
- Never describe the current pool as a custodial payout pool.
- Never enable automatic pooled payouts until the payout production gate in
  [pool-payout-production-plan.md](pool-payout-production-plan.md) is complete.
- Never call a release production-ready while `SHA256SUMS.asc`, release notes,
  and verification instructions are missing or incomplete.

## Quick Operator Status

On each Ubuntu seed or pool server, run:

```bash
sudo /usr/local/bin/bitstar-operator-status
```

If the helper is not installed yet:

```bash
cd contrib/bitstar/ops
sudo ./install-ops-hardening.sh
```

The status helper checks:

- service activity for `bitstard`
- explorer, pool, healthcheck, and backup timers when present
- local node RPC height, best hash, connection count, chain, IBD status, and
  warnings
- local listening ports for BitStar services
- pool dry-run ledger backup and restore-drill status when present

The helper does not read wallet keys, private keys, or RPC passwords directly.
It uses the local node configuration file already present on the server.

## Daily Checks

Run these once per day and after every deployment:

```bash
sudo /usr/local/bin/bitstar-operator-status
```

Then compare both seed nodes:

```bash
bitstar-cli -conf=/etc/bitstar/bitstar.conf -datadir=/var/lib/bitstar getblockcount
bitstar-cli -conf=/etc/bitstar/bitstar.conf -datadir=/var/lib/bitstar getbestblockhash
bitstar-cli -conf=/etc/bitstar/bitstar.conf -datadir=/var/lib/bitstar getconnectioncount
```

Healthy result:

- `bitstard.service` is active
- `bitstar-healthcheck.timer` is active
- seed1 and seed2 have matching or naturally converging height
- seed1 and seed2 have the same best hash after sync
- public P2P listens on `21333`
- RPC listens only on `127.0.0.1:21332`
- disk, memory, and CPU alerts are not firing

## Public Reachability Checks

From an outside machine:

```powershell
Test-NetConnection seed1.bitstarcoin.org -Port 21333
Test-NetConnection seed2.bitstarcoin.org -Port 21333
Test-NetConnection pool.bitstarcoin.org -Port 3333
```

Expected result: `TcpTestSucceeded : True`.

Check the public explorer API:

```bash
curl -fsS http://seed2.bitstarcoin.org:8090/healthz
curl -fsS http://seed2.bitstarcoin.org:8090/api/summary
curl -fsS http://seed2.bitstarcoin.org:8090/api/pool
```

## Service Restart Procedure

Restart only the service that needs attention.

Seed node:

```bash
sudo systemctl restart bitstard.service
sudo systemctl start bitstar-healthcheck.service
sudo journalctl -u bitstard -n 80 --no-pager
```

Explorer API:

```bash
sudo systemctl restart bitstar-explorer-api.service
sudo journalctl -u bitstar-explorer-api -n 80 --no-pager
curl -fsS http://127.0.0.1:8090/healthz
```

Solo/test pool:

```bash
sudo systemctl restart bitstar-stratum-pool.service
sudo journalctl -u bitstar-stratum-pool -n 80 --no-pager
sudo cat /var/lib/bitstar/pool-stats.json
```

## Clean Shutdown Procedure

Use clean shutdowns before package upgrades or VPS maintenance:

```bash
sudo systemctl stop bitstar-stratum-pool.service || true
sudo systemctl stop bitstar-explorer-api.service || true
sudo systemctl stop bitstard.service
```

Wait until `bitstard` exits cleanly, then start in reverse order:

```bash
sudo systemctl start bitstard.service
sudo systemctl start bitstar-explorer-api.service || true
sudo systemctl start bitstar-stratum-pool.service || true
sudo systemctl start bitstar-healthcheck.service
```

## Pool Backup And Restore Drill

On the pool host:

```bash
sudo systemctl start bitstar-pool-ledger-backup.service
sudo journalctl -u bitstar-pool-ledger-backup -n 40 --no-pager
sudo -u bitstar /usr/local/bin/bitstar-pool-ledger-backup.py --json restore-drill
sudo cat /var/lib/bitstar/pool-ledger-backup-status.json
```

Healthy result:

- SQLite verification succeeds
- restore drill succeeds
- backup status is updated
- public `/api/pool` reports sanitized backup status

Do not restore over the live dry-run ledger unless the pool is stopped and the
operator has identified the exact backup file to restore.

## Release Verification Procedure

For every public release, verify artifacts before installing them on seed nodes
or asking users to download them.

Windows user check:

```powershell
powershell -ExecutionPolicy Bypass -File .\verify-checksums.ps1 .\SHA256SUMS
gpg --verify .\SHA256SUMS.asc .\SHA256SUMS
powershell -ExecutionPolicy Bypass -File .\check-release-readiness.ps1 -ReleaseDir .\
```

Linux user check:

```bash
sh ./verify-checksums.sh SHA256SUMS
gpg --verify SHA256SUMS.asc SHA256SUMS
./check-release-readiness.sh --release-dir .
```

For the current bootstrap release, `SHA256SUMS` exists but the signed manifest
is still pending. That means the release is checksum-verifiable but not yet a
fully signed production release.

Before promoting a release, record:

- source tag
- source commit
- artifact filenames
- SHA256 values
- release signing key fingerprint
- release readiness gate result
- verification result on Windows
- verification result on Linux
- known limitations and warnings

See [release-verification.md](release-verification.md) and
[release-checklist.md](release-checklist.md). See
[release-key-ceremony.md](release-key-ceremony.md) before creating or rotating
the release signing key.

## Incident Response

### RPC Port Is Public

1. Close port `21332/tcp` immediately in the VPS firewall and host firewall.
2. Rotate RPC credentials.
3. Restart `bitstard`.
4. Check logs for unknown RPC access.
5. Publish a short incident note if public users could be affected.

### Seed Nodes Disagree

1. Stop public mining announcements.
2. Compare `getblockcount` and `getbestblockhash` on both seeds.
3. Check peer count and logs.
4. Keep the chain with the most valid work; do not manually edit chain data.
5. Publish the observed best hash after convergence.

### Pool Rejects Too Many Shares

1. Confirm miners use `sha256d`.
2. Confirm usernames are valid `bst1` addresses.
3. Check configured share difficulty.
4. Check `bitstard` sync status and `getblocktemplate`.
5. Keep public messaging clear: shares are test signals, not balances.

### Backup Or Restore Drill Fails

1. Stop any move toward production pooled payouts.
2. Run manual backup verification.
3. Check disk space and file permissions.
4. Fix backup automation.
5. Repeat restore drill before calling the pool baseline healthy.

## Weekly Checks

- Apply OS security updates or confirm the patch schedule.
- Review `journalctl` for repeated restarts or warnings.
- Confirm alert emails are still arriving.
- Confirm DNS still resolves seed and pool hostnames correctly.
- Confirm GitHub release links and website links still point to the intended
  release.
- Invite at least one independent operator to run a node and report height/hash.

## Production Exit Criteria

This runbook becomes production-grade only after:

- release artifacts are signed and independently verified
- seed nodes have independent third-party peers
- explorer supports stable block, transaction, and address lookup
- the pool either remains clearly solo/test or completes production payout
  accounting review
- the current bootstrap chain has a published continue/reset decision
- external review has checked consensus parameters and operational controls
