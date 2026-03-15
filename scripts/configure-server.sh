#!/usr/bin/env bash
# Generate WireGuard server keys and create /etc/wireguard/wg0.conf
set -euo pipefail

WG_PORT="${WG_PORT:-51820}"
WG_SERVER_IP="${WG_SERVER_IP:-10.0.0.1}"
WG_SUBNET="${WG_SUBNET:-10.0.0.0/24}"

# Detect primary network interface
IFACE=$(ip route | grep default | awk '{print $5}' | head -1)
echo "==> Detected network interface: $IFACE"

echo "==> Generating server keys..."
PRIVATE_KEY=$(wg genkey)
PUBLIC_KEY=$(echo "$PRIVATE_KEY" | wg pubkey)

# Save public key locally for the Python manager
mkdir -p config
echo "$PUBLIC_KEY" > config/server_public.key
echo "    Public key saved to config/server_public.key"

echo "==> Writing /etc/wireguard/wg0.conf..."
sudo mkdir -p /etc/wireguard

sudo tee /etc/wireguard/wg0.conf > /dev/null <<EOF
[Interface]
Address = ${WG_SERVER_IP}/24
SaveConfig = true
ListenPort = ${WG_PORT}
PrivateKey = ${PRIVATE_KEY}

PostUp = ufw route allow in on wg0 out on ${IFACE}
PostUp = iptables -t nat -I POSTROUTING -o ${IFACE} -j MASQUERADE
PreDown = ufw route delete allow in on wg0 out on ${IFACE}
PreDown = iptables -t nat -D POSTROUTING -o ${IFACE} -j MASQUERADE
EOF

sudo chmod 600 /etc/wireguard/wg0.conf

echo "==> Server configured."
echo "    Public key: $PUBLIC_KEY"
echo ""
echo "    Next steps:"
echo "      bash scripts/ufw-rules.sh"
echo "      bash scripts/start-wg.sh"
