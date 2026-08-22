# BitStar Explorer API

This is a small read-only explorer API for a BitStar seed node. It calls
`bitstar-cli` locally and does not expose the node RPC port.

Public endpoints:

- `GET /healthz`
- `GET /api/summary`
- `GET /api/block/<height-or-hash>`
- `GET /api/pool`

`/api/pool` reads the local pool stats file, defaults to
`/var/lib/bitstar/pool-stats.json`, and returns a sanitized public summary.
It does not expose node RPC credentials, miner IP addresses, or the private RPC
port.

Example deployment:

```bash
sudo install -d -o bitstar -g bitstar -m 0755 /opt/bitstar-explorer
sudo install -o bitstar -g bitstar -m 0755 bitstar-explorer-api.py /opt/bitstar-explorer/bitstar-explorer-api.py
sudo install -o root -g root -m 0644 bitstar-explorer-api.service /etc/systemd/system/bitstar-explorer-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now bitstar-explorer-api
sudo ufw allow 8090/tcp
```

The first public BitStar explorer route is published at:

```text
https://bitstarcoin.org/explorer
```
