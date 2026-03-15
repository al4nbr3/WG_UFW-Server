#!/usr/bin/env bash
# Add a WireGuard peer to the live server from config/clients/<name>.json
set -euo pipefail

NAME="${1:-}"
if [[ -z "$NAME" ]]; then
    echo "Usage: bash scripts/add-client.sh <client-name>"
    exit 1
fi

RECORD="config/clients/${NAME}.json"
if [[ ! -f "$RECORD" ]]; then
    echo "Client record not found: $RECORD"
    echo "Run first:  python wg_ufw_manager.py --add-client $NAME"
    exit 1
fi

PUBLIC_KEY=$(python3 -c "import json; d=json.load(open('$RECORD')); print(d['public_key'])")
IP=$(python3 -c "import json; d=json.load(open('$RECORD')); print(d['ip'].split('/')[0])")
PSK=$(python3 -c "import json; d=json.load(open('$RECORD')); print(d.get('preshared_key',''))")

echo "==> Adding peer '$NAME' (IP: $IP) to wg0..."

if [[ -n "$PSK" ]]; then
    sudo wg set wg0 peer "$PUBLIC_KEY" preshared-key <(echo "$PSK") allowed-ips "${IP}/32"
else
    sudo wg set wg0 peer "$PUBLIC_KEY" allowed-ips "${IP}/32"
fi

sudo wg-quick save wg0
echo "==> Peer '$NAME' added and config saved."
