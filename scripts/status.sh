#!/usr/bin/env bash
# Show WireGuard + UFW status
set -euo pipefail

echo "========== WireGuard Status =========="
sudo wg show || echo "WireGuard not running."

echo ""
echo "========== UFW Status =========="
sudo ufw status verbose

echo ""
echo "========== systemd Service =========="
systemctl status wg-quick@wg0 --no-pager || true
