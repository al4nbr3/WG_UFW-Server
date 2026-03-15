#!/usr/bin/env bash
# Remove a WireGuard peer from the live server
set -euo pipefail

NAME="${1:-}"
if [[ -z "$NAME" ]]; then
    echo "Usage: bash scripts/remove-client.sh <client-name>"
    exit 1
fi

RECORD="config/clients/${NAME}.json"
if [[ ! -f "$RECORD" ]]; then
    echo "Client record not found: $RECORD"
    exit 1
fi

PUBLIC_KEY=$(python3 -c "import json; d=json.load(open('$RECORD')); print(d['public_key'])")

echo "==> Removing peer '$NAME' from wg0..."
sudo wg set wg0 peer "$PUBLIC_KEY" remove
sudo wg-quick save wg0
echo "==> Peer '$NAME' removed."
