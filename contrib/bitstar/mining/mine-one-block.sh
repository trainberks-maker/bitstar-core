#!/usr/bin/env bash
set -euo pipefail

ADDRESS="${1:-${BITSTAR_MINING_ADDRESS:-}}"
BLOCKS="${BITSTAR_BLOCKS:-1}"
MAX_TRIES="${BITSTAR_MAX_TRIES:-50000000}"
CLI="${BITSTAR_CLI:-/usr/local/bin/bitstar-cli}"
DATADIR="${BITSTAR_DATADIR:-/var/lib/bitstar}"
CONF="${BITSTAR_CONF:-/etc/bitstar/bitstar.conf}"

if [[ -z "$ADDRESS" ]]; then
  echo "Usage: BITSTAR_MINING_ADDRESS=bst1... $0"
  echo "   or: $0 bst1..."
  exit 2
fi

if [[ "$ADDRESS" != bst1* ]]; then
  echo "Refusing to mine: address must start with bst1"
  exit 2
fi

if ! [[ "$BLOCKS" =~ ^[0-9]+$ ]] || (( BLOCKS < 1 )); then
  echo "Refusing to mine: BITSTAR_BLOCKS must be a positive integer"
  exit 2
fi

if (( BLOCKS > 10 )) && [[ "${BITSTAR_ALLOW_MULTI_BLOCK:-0}" != "1" ]]; then
  echo "Refusing to mine more than 10 blocks without BITSTAR_ALLOW_MULTI_BLOCK=1"
  exit 2
fi

if ! [[ "$MAX_TRIES" =~ ^[0-9]+$ ]] || (( MAX_TRIES < 1 )); then
  echo "Refusing to mine: BITSTAR_MAX_TRIES must be a positive integer"
  exit 2
fi

ARGS=("-datadir=$DATADIR" "-conf=$CONF")

echo "BitStar controlled mining"
echo "Address: $ADDRESS"
echo "Blocks:  $BLOCKS"

HEIGHT_BEFORE="$("$CLI" "${ARGS[@]}" getblockcount)"
echo "Height before: $HEIGHT_BEFORE"

"$CLI" "${ARGS[@]}" generatetoaddress "$BLOCKS" "$ADDRESS" "$MAX_TRIES"

HEIGHT_AFTER="$("$CLI" "${ARGS[@]}" getblockcount)"
echo "Height after:  $HEIGHT_AFTER"
echo "Done. Coinbase rewards mature after 100 confirmations."
