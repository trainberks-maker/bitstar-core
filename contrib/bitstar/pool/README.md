# BitStar Stratum Solo Test Pool

This directory contains a minimal Stratum V1 server for early BitStar mining
compatibility tests. It is not a production pooled-mining platform.

The server works as a solo test pool:

- miners connect over Stratum on TCP `3333`
- the worker username must be a valid BitStar payout address
- the pool builds block templates through local `bitstar-cli`
- the default bootstrap share difficulty is `0.00010`
- if a miner finds a valid block, the coinbase output pays the miner address
- no payout accounting, balances, web dashboard, vardiff, or custody is provided
- a local operator stats file tracks submitted, rejected, accepted, and
  block-candidate shares

## Install On A Seed Or Pool VPS

Run these commands on the Ubuntu server that already has `bitstard` installed:

```bash
sudo install -o root -g root -m 0755 bitstar-stratum-pool.py /usr/local/bin/bitstar-stratum-pool.py
sudo install -o root -g root -m 0644 bitstar-stratum-pool.service /etc/systemd/system/bitstar-stratum-pool.service
sudo systemctl daemon-reload
sudo systemctl enable --now bitstar-stratum-pool.service
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

Important fields:

- `submitted_shares`: miner shares received by the pool
- `accepted_shares`: shares that met the pool share difficulty
- `rejected_low_difficulty`: shares below the configured pool share difficulty
- `candidate_blocks`: shares strong enough to be submitted as possible blocks
- `submitblock_success`: candidate blocks accepted by `bitstard`

Miner output such as `Submitted Diff ...` only means the miner sent shares to
the Stratum server. It does not mean a BitStar block was mined unless the pool
stats show `candidate_blocks` and `submitblock_success`, and the public chain
height increases.

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
