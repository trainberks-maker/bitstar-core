#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SWAP_SIZE="${BITSTAR_SWAP_SIZE:-2G}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root." >&2
  exit 1
fi

install_file() {
  local src="$1"
  local dst="$2"
  local mode="$3"
  local owner="${4:-root}"
  local group="${5:-root}"
  install -D -o "$owner" -g "$group" -m "$mode" "$src" "$dst"
}

install_file "$SCRIPT_DIR/ssh-hardening.conf" /etc/ssh/sshd_config.d/99-bitstar-hardening.conf 0644
sshd -t
systemctl reload ssh || systemctl reload sshd

install_file "$SCRIPT_DIR/bitstar-logrotate" /etc/logrotate.d/bitstar 0644
install_file "$SCRIPT_DIR/bitstar-healthcheck.sh" /usr/local/bin/bitstar-healthcheck 0755
install_file "$SCRIPT_DIR/bitstar-operator-status.sh" /usr/local/bin/bitstar-operator-status 0755
install_file "$SCRIPT_DIR/bitstar-healthcheck.service" /etc/systemd/system/bitstar-healthcheck.service 0644
install_file "$SCRIPT_DIR/bitstar-healthcheck.timer" /etc/systemd/system/bitstar-healthcheck.timer 0644

install -d -o root -g root -m 0755 /etc/systemd/system/bitstard.service.d
install_file "$SCRIPT_DIR/bitstard-hardening.conf" /etc/systemd/system/bitstard.service.d/10-hardening.conf 0644

for service in bitstar-stratum-pool.service bitstar-explorer-api.service; do
  if systemctl list-unit-files "$service" --no-legend | grep -q "$service"; then
    install -d -o root -g root -m 0755 "/etc/systemd/system/$service.d"
    install_file "$SCRIPT_DIR/bitstar-worker-hardening.conf" "/etc/systemd/system/$service.d/10-hardening.conf" 0644
  fi
done

if ! swapon --show=NAME --noheadings | grep -qx /swapfile; then
  if [ ! -f /swapfile ]; then
    fallocate -l "$SWAP_SIZE" /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
    chmod 600 /swapfile
    mkswap /swapfile
  fi
  swapon /swapfile
fi

if ! grep -Eq '^/swapfile[[:space:]]+none[[:space:]]+swap[[:space:]]+' /etc/fstab; then
  printf '%s\n' '/swapfile none swap sw 0 0' >> /etc/fstab
fi

systemctl daemon-reload
systemctl enable --now bitstar-healthcheck.timer

systemctl restart bitstard.service

for service in bitstar-stratum-pool.service bitstar-explorer-api.service; do
  if systemctl list-unit-files "$service" --no-legend | grep -q "$service"; then
    systemctl restart "$service"
  fi
done

health_ok=0
for _ in $(seq 1 30); do
  if systemctl start bitstar-healthcheck.service; then
    health_ok=1
    break
  fi
  sleep 2
done

if [ "$health_ok" -ne 1 ]; then
  journalctl -u bitstar-healthcheck.service -n 50 --no-pager
  exit 1
fi

systemctl --no-pager --full status bitstar-healthcheck.timer bitstar-healthcheck.service || true
