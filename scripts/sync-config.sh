#!/usr/bin/env bash
# Apply edits in /etc/wireguard/wg0.conf to the running wg0 interface
# WITHOUT calling `wg-quick down` (which, with SaveConfig=true, would
# overwrite manual edits with the current runtime state on the way down).
#
# Run this on the WireGuard server.
set -euo pipefail

CONF="/etc/wireguard/wg0.conf"

if [[ ! -f "${CONF}" ]]; then
    echo "ERROR: ${CONF} not found." >&2
    exit 1
fi

echo "==> Applying ${CONF} to the live wg0 interface"
# Wrap in a sudo-bash so the process substitution fd is created in the
# privileged shell (sudo can't read /dev/fd/<n> from the calling user).
sudo bash -c "wg syncconf wg0 <(wg-quick strip ${CONF})"

echo ""
echo "==> wg show"
sudo wg show wg0
