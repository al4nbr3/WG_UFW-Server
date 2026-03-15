#!/usr/bin/env bash
# Install WireGuard and UFW on Ubuntu 24.04
set -euo pipefail

echo "==> Updating package list..."
sudo apt update

echo "==> Installing WireGuard..."
sudo apt install -y wireguard

echo "==> Installing UFW..."
sudo apt install -y ufw

echo "==> Enabling IP forwarding..."
if ! grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
fi
if ! grep -q "^net.ipv6.conf.all.forwarding=1" /etc/sysctl.conf; then
    echo "net.ipv6.conf.all.forwarding=1" | sudo tee -a /etc/sysctl.conf
fi
sudo sysctl -p

echo ""
echo "==> Installation complete."
echo "    Next: run  bash scripts/configure-server.sh"
