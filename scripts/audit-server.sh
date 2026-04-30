#!/usr/bin/env bash
# Audit V10L3T4 services: WireGuard, Tor, Privoxy, UFW, and routing.
# Run this on the server.
set -euo pipefail

section() { echo ""; echo "========== $1 =========="; }

section "Host"
hostname
uname -a

section "WireGuard (wg0)"
systemctl is-enabled wg-quick@wg0 || true
systemctl is-active  wg-quick@wg0 || true
sudo wg show wg0 || echo "wg0 not up"

section "Tor"
systemctl is-enabled tor || true
systemctl is-active  tor || true
sudo grep -vE '^\s*(#|$)' /etc/tor/torrc

section "Privoxy"
systemctl is-enabled privoxy || true
systemctl is-active  privoxy || true
sudo grep -E '^(listen-address|forward-socks5t)' /etc/privoxy/config

section "UFW"
sudo ufw status verbose

section "Networking"
echo "ip_forward: $(cat /proc/sys/net/ipv4/ip_forward)"
ip -brief addr
echo ""
ip route
