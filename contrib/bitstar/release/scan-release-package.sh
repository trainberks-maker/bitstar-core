#!/usr/bin/env sh
set -eu

release_dir="."
artifacts=""
failed=0
warned=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --release-dir)
      release_dir="${2:?missing value for --release-dir}"
      shift 2
      ;;
    --artifact)
      artifacts="${artifacts}
${2:?missing value for --artifact}"
      shift 2
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

is_text_entry() {
  printf '%s' "$1" | grep -Eiq '\.(md|txt|conf|service|timer|sh|bat|ps1|json|yml|yaml|ini|env|log)$'
}

scan_entry_path() {
  artifact_name="$1"
  entry_name=$(printf '%s' "$2" | tr '\\' '/')
  forbidden='(^|/)(wallet\.dat|blocks|chainstate|indexes|wallets|debug\.log|mempool\.dat|peers\.dat|banlist\.dat|\.cookie|\.ssh|id_rsa|id_dsa|id_ecdsa|id_ed25519|authorized_keys|known_hosts)(/|$)|\.(pem|p12|pfx)$'

  if printf '%s' "$entry_name" | grep -Eiq "$forbidden"; then
    fail "$artifact_name contains private node, wallet, or credential path: $entry_name"
  fi
}

scan_content_stream() {
  artifact_name="$1"
  entry_name="$2"
  extractor="$3"
  strict_config="$4"

  if sh -c "$extractor" | grep -Eiq -- '-----BEGIN (OPENSSH|RSA|DSA|EC|.*PRIVATE) PRIVATE KEY-----'; then
    fail "$artifact_name entry $entry_name contains private key material"
  fi

  [ "$strict_config" -eq 1 ] || return 0

  if sh -c "$extractor" | grep -Eiq '^[[:space:]]*(rpcpassword|rpcauth)[[:space:]]*=[[:space:]]*[^#[:space:]]+'; then
    fail "$artifact_name entry $entry_name contains hard-coded RPC credential"
  fi

  if sh -c "$extractor" | grep -Eiq '^[[:space:]]*(github_token|digitalocean_token|cloudflare_api_token|openai_api_key|api_key|secret_key|password)[[:space:]]*=[[:space:]]*[^#[:space:]]+'; then
    fail "$artifact_name entry $entry_name contains hard-coded token or password"
  fi

  if sh -c "$extractor" | grep -Eiq '^[[:space:]]*rpcbind[[:space:]]*=[[:space:]]*(0\.0\.0\.0|\*)'; then
    fail "$artifact_name entry $entry_name contains unsafe public RPC bind"
  fi

  if sh -c "$extractor" | grep -Eiq '^[[:space:]]*rpcallowip[[:space:]]*=[[:space:]]*(0\.0\.0\.0/0|::/0|\*)'; then
    fail "$artifact_name entry $entry_name contains unsafe public RPC allowlist"
  fi
}

scan_tar_gz() {
  archive="$1"
  artifact_name=$(basename "$archive")

  if ! entries=$(tar -tzf "$archive"); then
    fail "could not list archive: $artifact_name"
    return
  fi

  oldifs=$IFS
  IFS='
'
  for entry in $entries; do
    [ -n "$entry" ] || continue
    scan_entry_path "$artifact_name" "$entry"
    if is_text_entry "$entry"; then
      escaped_archive=$(printf '%s' "$archive" | sed "s/'/'\\\\''/g")
      escaped_entry=$(printf '%s' "$entry" | sed "s/'/'\\\\''/g")
      case "$entry" in
        *.md|*.MD|*.txt|*.TXT) strict_config=0 ;;
        *) strict_config=1 ;;
      esac
      scan_content_stream "$artifact_name" "$entry" "tar -xOzf '$escaped_archive' '$escaped_entry' 2>/dev/null" "$strict_config"
    fi
  done
  IFS=$oldifs

  pass "package hygiene scan completed: $artifact_name"
}

scan_zip() {
  archive="$1"
  artifact_name=$(basename "$archive")

  if command -v unzip >/dev/null 2>&1; then
    entries=$(unzip -Z1 "$archive")
  elif command -v zipinfo >/dev/null 2>&1; then
    entries=$(zipinfo -1 "$archive")
  else
    warn "unzip/zipinfo missing; cannot inspect zip: $artifact_name"
    return
  fi

  oldifs=$IFS
  IFS='
'
  for entry in $entries; do
    [ -n "$entry" ] || continue
    scan_entry_path "$artifact_name" "$entry"
    if is_text_entry "$entry"; then
      escaped_archive=$(printf '%s' "$archive" | sed "s/'/'\\\\''/g")
      escaped_entry=$(printf '%s' "$entry" | sed "s/'/'\\\\''/g")
      case "$entry" in
        *.md|*.MD|*.txt|*.TXT) strict_config=0 ;;
        *) strict_config=1 ;;
      esac
      scan_content_stream "$artifact_name" "$entry" "unzip -p '$escaped_archive' '$escaped_entry' 2>/dev/null" "$strict_config"
    fi
  done
  IFS=$oldifs

  pass "package hygiene scan completed: $artifact_name"
}

scan_archive() {
  archive="$1"
  case "$archive" in
    *.zip|*.ZIP)
      scan_zip "$archive"
      ;;
    *.tar.gz|*.tgz|*.TAR.GZ|*.TGZ)
      scan_tar_gz "$archive"
      ;;
    *)
      warn "skipping unsupported artifact: $(basename "$archive")"
      ;;
  esac
}

echo "BitStar release package hygiene scan"
echo "Release directory: $release_dir"

found=0
if [ -n "$artifacts" ]; then
  oldifs=$IFS
  IFS='
'
  for artifact in $artifacts; do
    [ -n "$artifact" ] || continue
    path="${release_dir%/}/$artifact"
    if [ -f "$path" ]; then
      found=1
      scan_archive "$path"
    else
      fail "artifact not found: $artifact"
    fi
  done
  IFS=$oldifs
else
  for path in "$release_dir"/*.zip "$release_dir"/*.tar.gz "$release_dir"/*.tgz; do
    [ -f "$path" ] || continue
    found=1
    scan_archive "$path"
  done
fi

if [ "$found" -eq 0 ]; then
  fail "no release archives found"
fi

if [ "$failed" -eq 1 ]; then
  echo "Result: package hygiene scan failed."
  exit 1
fi

if [ "$warned" -eq 1 ]; then
  echo "Result: package hygiene scan completed with warnings."
  exit 0
fi

echo "Result: package hygiene scan passed."
