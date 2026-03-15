#!/usr/bin/env bash
# Start WireGuard and enable on boot
set -euo pipefail

echo "==> Starting WireGuard (wg0)..."
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
sudo systemctl status wg-quick@wg0 --no-pager
