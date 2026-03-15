#!/usr/bin/env bash
# Backup WireGuard config and client records
set -euo pipefail

BACKUP_DIR="backups/$(date +%Y%m%dT%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "==> Backing up /etc/wireguard/wg0.conf..."
sudo cp /etc/wireguard/wg0.conf "$BACKUP_DIR/wg0.conf"
sudo chown "$USER" "$BACKUP_DIR/wg0.conf"

echo "==> Backing up client records..."
if [[ -d config/clients ]]; then
    cp -r config/clients "$BACKUP_DIR/"
fi

if [[ -f config/server_public.key ]]; then
    cp config/server_public.key "$BACKUP_DIR/"
fi

echo "==> Backup saved to: $BACKUP_DIR"
ls -lh "$BACKUP_DIR"
