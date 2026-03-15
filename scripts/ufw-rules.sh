#!/usr/bin/env bash
# Apply UFW rules required for WireGuard
set -euo pipefail

WG_PORT="${WG_PORT:-51820}"
IFACE=$(ip route | grep default | awk '{print $5}' | head -1)

echo "==> Applying UFW rules (interface: $IFACE, WireGuard port: $WG_PORT)..."

sudo ufw allow "${WG_PORT}/udp"
sudo ufw allow OpenSSH
sudo ufw route allow in on wg0 out on "$IFACE"
sudo ufw --force enable

echo "==> UFW rules applied."
sudo ufw status verbose
