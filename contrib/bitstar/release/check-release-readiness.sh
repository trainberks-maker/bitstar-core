#!/usr/bin/env sh
set -eu

release_dir="."
manifest="SHA256SUMS"
allow_unsigned_bootstrap=0
failed=0
warned=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --release-dir)
      release_dir="${2:?missing value for --release-dir}"
      shift 2
      ;;
    --manifest)
      manifest="${2:?missing value for --manifest}"
      shift 2
      ;;
    --allow-unsigned-bootstrap)
      allow_unsigned_bootstrap=1
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

fail() {
  echo "FAIL    $1"
  failed=1
}

warn() {
  echo "WARN    $1"
  warned=1
}

pass() {
  echo "OK      $1"
}

hash_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print tolower($1)}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print tolower($1)}'
  elif command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 "$1" | awk '{print tolower($NF)}'
  else
    echo "missing"
  fi
}

manifest_path="${release_dir%/}/$manifest"
signature_path="$manifest_path.asc"

echo "BitStar release readiness check"
echo "Release directory: $release_dir"

if [ ! -f "$manifest_path" ]; then
  fail "manifest not found: $manifest_path"
  echo "Result: not production-ready."
  exit 1
fi

pass "manifest present: $manifest"

checked=0
while IFS= read -r line || [ -n "$line" ]; do
  line=$(printf '%s' "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  [ -n "$line" ] || continue
  case "$line" in \#*) continue ;; esac

  expected=$(printf '%s' "$line" | awk '{print tolower($1)}')
  name=$(printf '%s' "$line" | sed 's/^[^[:space:]]*[[:space:]]*//;s/^\*//')

  if ! printf '%s' "$expected" | grep -Eq '^[0-9a-f]{64}$'; then
    fail "invalid manifest line: $line"
    continue
  fi

  artifact="${release_dir%/}/$name"
  if [ ! -f "$artifact" ]; then
    fail "artifact missing: $name"
    continue
  fi

  actual=$(hash_file "$artifact")
  if [ "$actual" = "missing" ]; then
    fail "sha256 tool missing"
    continue
  fi

  checked=$((checked + 1))
  if [ "$actual" = "$expected" ]; then
    pass "checksum verified: $name"
  else
    fail "checksum mismatch: $name"
  fi
done < "$manifest_path"

if [ "$checked" -eq 0 ]; then
  fail "manifest contains no artifact entries"
fi

if command -v gpg >/dev/null 2>&1; then
  pass "gpg available: $(command -v gpg)"
  have_gpg=1
else
  warn "gpg not found; install GnuPG before production signing"
  have_gpg=0
fi

if [ ! -f "$signature_path" ]; then
  if [ "$allow_unsigned_bootstrap" -eq 1 ]; then
    warn "signature missing: $manifest.asc; allowed only for bootstrap status"
  else
    fail "signature missing: $manifest.asc"
  fi
elif [ "$have_gpg" -eq 0 ]; then
  fail "signature exists but cannot be verified because gpg is missing"
elif gpg --verify "$signature_path" "$manifest_path"; then
  pass "GPG signature verified: $manifest.asc"
else
  fail "GPG signature verification failed"
fi

if [ "$failed" -eq 1 ]; then
  echo "Result: not production-ready."
  exit 1
fi

if [ "$warned" -eq 1 ]; then
  echo "Result: bootstrap-verifiable only, not production signed."
  exit 0
fi

echo "Result: release artifacts are signed and checksum verified."
