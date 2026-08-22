# BitStar Operations Hardening

This document records the operational baseline for public BitStar seed nodes,
the explorer API, and the public solo/test pool.

For the practical daily operating procedure, restarts, incident response,
backup drills, and release verification checks, use
[operator-runbook.md](operator-runbook.md).

## Live Baseline

Checked on August 21, 2026.

### seed1.bitstarcoin.org

- Public IP: `134.209.68.145`
- P2P: `0.0.0.0:21333` and `[::]:21333`
- RPC: `127.0.0.1:21332`
- ZMQ/internal: `127.0.0.1:21334`
- `bitstard`: active
- Firewall allows: OpenSSH, `21333/tcp`
- Disk: 77 GB total, about 6% used
- Memory: 4 GB total, about 3.3 GB available

### seed2.bitstarcoin.org

- Public IP: `134.122.66.31`
- P2P: `0.0.0.0:21333` and `[::]:21333`
- RPC: `127.0.0.1:21332`
- ZMQ/internal: `127.0.0.1:21334`
- Explorer API: `0.0.0.0:8090`
- Stratum test pool: `0.0.0.0:3333`
- `bitstard`: active
- `bitstar-stratum-pool`: active
- `bitstar-explorer-api`: active
- Firewall allows: OpenSSH, `21333/tcp`, `3333/tcp`, `8090/tcp`
- Disk: 87 GB total, about 3% used
- Memory: 2 GB total, about 1.5 GB available

Both nodes were synchronized at height `5` with best block:

```text
00000e7ed0c7df4e0db2d66c8d0031042e1ad66f5a8e3bf3e23a8e6a151c502d
```

## Good Baseline

- RPC is bound to `127.0.0.1`, not public internet.
- P2P port `21333` is public, as required for public nodes.
- seed1 and seed2 are connected and synchronized.
- seed2 exposes the public test pool on `3333/tcp`.
- seed2 exposes the current explorer API on `8090/tcp`.
- Firewalls are enabled.
- Disk usage is low on both nodes.

## Hardening Required Before Production

### SSH

- require SSH keys
- disable password login
- create a non-root admin user
- disable direct root login after the admin user is verified
- keep emergency console access through the VPS provider

### Firewall

- keep `21332/tcp` RPC closed publicly
- keep `21334/tcp` internal only
- keep `21333/tcp` open publicly
- keep `3333/tcp` open only while the public test pool is intentionally active
- review whether `8090/tcp` should remain public or move behind a reverse proxy

### System Services

- ensure all BitStar services restart automatically
- run services under the `bitstar` user
- add systemd restart limits to avoid tight crash loops
- enable log rotation for:
  - BitStar debug logs
  - explorer API logs
  - Stratum pool logs

### Updates And Backups

- enable unattended security updates or document a patch schedule
- create VPS snapshots before major release changes
- back up wallet files only when a server wallet is intentionally used
- do not store long-term private keys on public seed nodes

### Monitoring

Monitor at minimum:

- node is running
- P2P port `21333` reachable
- chain height increasing or matching expected network height
- seed1 and seed2 best block hash match
- disk usage below 80%
- memory usage below 85%
- CPU usage below 70% for sustained periods
- explorer API returns HTTP 200
- pool port `3333` reachable while pool is advertised
- `bitstar-operator-status` produces a clean daily status report on each host

### Pool Safety

The current pool is a solo/test pool. It should not be marketed as a production
pool until it has:

- dashboard
- worker stats
- share history
- accepted/rejected share counters
- payout accounting
- payout maturity logic
- payout transaction history
- abuse/rate limits
- operator contact and incident process

### Explorer Safety

The current explorer is a basic status explorer. It should not be described as a
professional explorer until it has:

- block search by height and hash
- transaction search
- address search
- API caching
- error pages
- backend monitoring
- database or indexer design for historical queries

## Production Rule

Never expose BitStar RPC (`21332/tcp`) to the public internet. Pools, explorers,
and automation should talk to a local node RPC over `127.0.0.1` or through a
private network only.

## Installable Baseline

The repository includes an idempotent installer for the baseline hardening in:

```text
contrib/bitstar/ops/install-ops-hardening.sh
```

It installs SSH hardening, logrotate, a healthcheck timer, systemd restart
limits, the `bitstar-operator-status` helper, and a swapfile for memory safety.
