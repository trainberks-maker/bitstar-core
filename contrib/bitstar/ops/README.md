# BitStar Operations Scripts

These scripts install the baseline VPS hardening used by the public BitStar
bootstrap nodes.

## What It Installs

- SSH hardening drop-in
- BitStar debug log rotation
- BitStar healthcheck script and systemd timer
- BitStar operator status helper
- systemd restart-limit drop-ins
- 2 GB swapfile, unless swap already exists

## Install

Run as root on a BitStar VPS:

```bash
cd contrib/bitstar/ops
sudo ./install-ops-hardening.sh
```

The script is idempotent and can be re-run after updates.

## Operator Status

After installation, run:

```bash
sudo /usr/local/bin/bitstar-operator-status
```

The helper reports service status, local RPC height/hash/connections, listening
ports, and pool backup/restore-drill status when present. It is intended for
the daily checks in `doc/bitstar/operator-runbook.md`.

## Safety Notes

- RPC must remain private on `127.0.0.1:21332`.
- P2P should remain public on `21333/tcp`.
- The public test pool, when enabled, listens on `3333/tcp`.
- The current explorer API, when enabled, listens on `8090/tcp`.
