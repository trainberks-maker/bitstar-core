#!/usr/bin/env sh
set -eu

gpg_key=""
output="bitstar-release-key.asc"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --key)
      gpg_key="${2:?missing value for --key}"
      shift 2
      ;;
    --output)
      output="${2:?missing value for --output}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ -z "$gpg_key" ]; then
  echo "Pass --key with the BitStar release key fingerprint, long key id, or user id." >&2
  exit 2
fi

if ! command -v gpg >/dev/null 2>&1; then
  echo "gpg was not found. Install GnuPG before exporting the public release key." >&2
  exit 2
fi

gpg --list-keys --keyid-format LONG "$gpg_key"
gpg --armor --export "$gpg_key" > "$output"

echo "Wrote public release key: $output"
echo "Release key fingerprint:"
gpg --fingerprint --keyid-format LONG "$gpg_key"
echo ""
echo "Safety: this exports only the public key. Never upload or paste the secret release key or passphrase."
