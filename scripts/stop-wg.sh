#!/usr/bin/env bash
# Stop WireGuard
set -euo pipefail

echo "==> Stopping WireGuard (wg0)..."
sudo systemctl stop wg-quick@wg0
sudo systemctl disable wg-quick@wg0
echo "==> WireGuard stopped and disabled."
