#!/usr/bin/env sh
set -eu

manifest="${1:-SHA256SUMS}"

if [ ! -f "$manifest" ]; then
  echo "Manifest not found: $manifest" >&2
  exit 2
fi

if command -v sha256sum >/dev/null 2>&1; then
  sha256sum -c "$manifest"
  exit $?
fi

if ! command -v openssl >/dev/null 2>&1; then
  echo "Install sha256sum or openssl to verify checksums." >&2
  exit 2
fi

status=0
checked=0
manifest_dir="$(dirname "$manifest")"

while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    ""|\#*) continue ;;
  esac

  expected="$(printf '%s\n' "$line" | awk '{print tolower($1)}')"
  file="$(printf '%s\n' "$line" | cut -d ' ' -f 2- | sed 's/^ *//; s/^\*//')"

  if [ -z "$expected" ] || [ -z "$file" ]; then
    echo "INVALID $line"
    status=1
    continue
  fi

  path="$manifest_dir/$file"
  if [ ! -f "$path" ]; then
    echo "MISSING $file"
    status=1
    continue
  fi

  actual="$(openssl dgst -sha256 "$path" | awk '{print tolower($NF)}')"
  checked=$((checked + 1))
  if [ "$actual" = "$expected" ]; then
    echo "OK      $file"
  else
    echo "FAILED  $file"
    status=1
  fi
done < "$manifest"

if [ "$checked" -eq 0 ]; then
  echo "No checksum entries were checked." >&2
  exit 2
fi

exit "$status"
