#!/usr/bin/env bash
set -euo pipefail

BITSTAR_CLI="${BITSTAR_CLI:-/usr/local/bin/bitstar-cli}"
BITSTAR_CONF="${BITSTAR_CONF:-/etc/bitstar/bitstar.conf}"
BITSTAR_DATADIR="${BITSTAR_DATADIR:-/var/lib/bitstar}"
MIN_CONNECTIONS="${BITSTAR_MIN_CONNECTIONS:-1}"

block_count="$("$BITSTAR_CLI" -conf="$BITSTAR_CONF" -datadir="$BITSTAR_DATADIR" getblockcount)"
best_hash="$("$BITSTAR_CLI" -conf="$BITSTAR_CONF" -datadir="$BITSTAR_DATADIR" getbestblockhash)"
connections="$("$BITSTAR_CLI" -conf="$BITSTAR_CONF" -datadir="$BITSTAR_DATADIR" getconnectioncount)"

if [ "$connections" -lt "$MIN_CONNECTIONS" ]; then
  echo "BitStar healthcheck failed: connections=$connections min=$MIN_CONNECTIONS height=$block_count best=$best_hash" >&2
  exit 2
fi

echo "BitStar healthcheck ok: height=$block_count best=$best_hash connections=$connections"
