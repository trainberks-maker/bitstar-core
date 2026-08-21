#!/usr/bin/env sh
set -eu

output="SHA256SUMS"
gpg_key=""
no_sign=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output)
      output="${2:?missing value for --output}"
      shift 2
      ;;
    --key)
      gpg_key="${2:?missing value for --key}"
      shift 2
      ;;
    --no-sign)
      no_sign=1
      shift
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

if [ "$#" -eq 0 ]; then
  set -- BitStar_*.zip BitStar_*.tar.gz
fi

tmp="${output}.tmp"
: > "$tmp"
checked=0

for artifact in "$@"; do
  [ -e "$artifact" ] || continue
  if [ ! -f "$artifact" ]; then
    echo "Artifact is not a regular file: $artifact" >&2
    rm -f "$tmp"
    exit 2
  fi

  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$artifact" >> "$tmp"
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$artifact" >> "$tmp"
  elif command -v openssl >/dev/null 2>&1; then
    hash="$(openssl dgst -sha256 "$artifact" | awk '{print tolower($NF)}')"
    printf '%s  %s\n' "$hash" "$(basename "$artifact")" >> "$tmp"
  else
    echo "Install sha256sum, shasum, or openssl to create checksums." >&2
    rm -f "$tmp"
    exit 2
  fi
  checked=$((checked + 1))
done

if [ "$checked" -eq 0 ]; then
  echo "No artifacts found. Pass package paths or run from a folder containing BitStar release packages." >&2
  rm -f "$tmp"
  exit 2
fi

mv "$tmp" "$output"
echo "Wrote $output with $checked artifact checksum(s)."

if [ "$no_sign" -eq 1 ]; then
  echo "Skipped GPG signing because --no-sign was set."
  exit 0
fi

if ! command -v gpg >/dev/null 2>&1; then
  echo "gpg was not found. Install GnuPG or run with --no-sign to create only SHA256SUMS." >&2
  exit 2
fi

if [ -n "$gpg_key" ]; then
  gpg --armor --detach-sign --local-user "$gpg_key" --output "${output}.asc" "$output"
else
  gpg --armor --detach-sign --output "${output}.asc" "$output"
fi

gpg --verify "${output}.asc" "$output"
echo "Wrote detached signature: ${output}.asc"
