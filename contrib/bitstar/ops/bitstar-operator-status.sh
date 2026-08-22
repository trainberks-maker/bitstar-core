#!/usr/bin/env bash
set -euo pipefail

BITSTAR_CLI="${BITSTAR_CLI:-/usr/local/bin/bitstar-cli}"
BITSTAR_CONF="${BITSTAR_CONF:-/etc/bitstar/bitstar.conf}"
BITSTAR_DATADIR="${BITSTAR_DATADIR:-/var/lib/bitstar}"
BACKUP_STATUS="${BITSTAR_POOL_BACKUP_STATUS:-/var/lib/bitstar/pool-ledger-backup-status.json}"

section() {
  printf '\n== %s ==\n' "$1"
}

unit_status() {
  local unit="$1"
  if systemctl list-unit-files "$unit" --no-legend 2>/dev/null | grep -q "$unit"; then
    printf '%-34s %s\n' "$unit" "$(systemctl is-active "$unit" 2>/dev/null || true)"
  else
    printf '%-34s %s\n' "$unit" "not-installed"
  fi
}

cli() {
  "$BITSTAR_CLI" -conf="$BITSTAR_CONF" -datadir="$BITSTAR_DATADIR" "$@"
}

section "Host"
hostnamectl --static 2>/dev/null || hostname
date -u +"%Y-%m-%dT%H:%M:%SZ"

section "Services"
unit_status bitstard.service
unit_status bitstar-healthcheck.timer
unit_status bitstar-healthcheck.service
unit_status bitstar-explorer-api.service
unit_status bitstar-stratum-pool.service
unit_status bitstar-pool-ledger-backup.timer
unit_status bitstar-pool-ledger-backup.service

section "Node RPC"
if [ ! -x "$BITSTAR_CLI" ]; then
  echo "bitstar-cli not executable at $BITSTAR_CLI"
else
  if cli getblockchaininfo >/tmp/bitstar-operator-chaininfo.$$ 2>/tmp/bitstar-operator-rpc-error.$$; then
    echo "height:      $(cli getblockcount)"
    echo "best hash:   $(cli getbestblockhash)"
    echo "connections: $(cli getconnectioncount)"
    if command -v python3 >/dev/null 2>&1; then
      python3 - "/tmp/bitstar-operator-chaininfo.$$" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"chain:       {data.get('chain', 'unknown')}")
print(f"ibd:         {data.get('initialblockdownload', 'unknown')}")
print(f"warnings:    {data.get('warnings', '')}")
PY
    fi
  else
    echo "RPC check failed:"
    cat /tmp/bitstar-operator-rpc-error.$$ || true
  fi
  rm -f /tmp/bitstar-operator-chaininfo.$$ /tmp/bitstar-operator-rpc-error.$$
fi

section "Listening Ports"
if command -v ss >/dev/null 2>&1; then
  ss -ltn | awk 'NR == 1 || /:21333|:21332|:21334|:3333|:8090/'
else
  echo "ss command not available"
fi

section "Pool Backup"
if [ -r "$BACKUP_STATUS" ] && command -v python3 >/dev/null 2>&1; then
  python3 - "$BACKUP_STATUS" <<'PY'
import json
import os
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

latest = data.get("latest_backup") or {}
print(f"available:              true")
print(f"last backup:            {latest.get('name', '')}")
print(f"last verify ok:         {data.get('last_verify_ok', '')}")
print(f"last restore drill ok:  {data.get('last_restore_drill_ok', '')}")
print(f"backup count:           {data.get('backup_count', '')}")
PY
elif [ -e "$BACKUP_STATUS" ]; then
  echo "backup status exists but is not readable by this user"
else
  echo "backup status not present on this host"
fi

section "Operator Reminder"
echo "RPC must stay private on 127.0.0.1:21332."
echo "P2P should be public on 21333/tcp."
echo "Treat pool counters as test signals, not balances."
