#!/usr/bin/env bash
# Cleanup remote host — stop/remove non-essential services and packages
# Keeps: SSH, NetworkManager, UFW, cron, rsyslog, core system
set -euo pipefail

echo "==> Stopping and disabling unnecessary services..."
SERVICES=(
    logstash
    suricata
    snort
    nmbd
    smbd
    cups
    cups-browsed
    bluetooth
    avahi-daemon
    colord
    ModemManager
    gnome-remote-desktop
    kerneloops
    packagekit
    fwupd
    spice-vdagent
    xrdp
)

for svc in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        echo "  Stopping: $svc"
        sudo systemctl stop "$svc" || true
    fi
    if systemctl is-enabled --quiet "$svc" 2>/dev/null; then
        echo "  Disabling: $svc"
        sudo systemctl disable "$svc" || true
    fi
done

echo ""
echo "==> Removing unnecessary packages..."
sudo apt remove -y --purge \
    logstash \
    suricata suricata-update \
    snort snort-common snort-rules-default oinkmaster \
    samba samba-common samba-common-bin nmbd \
    cups cups-daemon cups-browsed cups-client cups-common cups-bsd cups-filters \
    bluetooth bluez bluez-cups bluez-obexd \
    avahi-daemon \
    brave-browser \
    firefox \
    thunderbird thunderbird-locale-en thunderbird-locale-en-us \
    virtualbox virtualbox-dkms virtualbox-ext-pack virtualbox-qt \
    vagrant \
    rhythmbox rhythmbox-data rhythmbox-plugins \
    totem totem-common totem-plugins \
    transmission-gtk transmission-common \
    shotwell shotwell-common \
    vokoscreen-ng \
    simple-scan \
    colord colord-data \
    logstash \
    xrdp xorgxrdp \
    modemmanager \
    gamemode gamemode-daemon \
    gnome-games \
    deja-dup duplicity \
    remmina remmina-common remmina-plugin-rdp remmina-plugin-vnc \
    2>/dev/null || true

echo ""
echo "==> Removing unused dependencies..."
sudo apt autoremove -y
sudo apt clean

echo ""
echo "==> Verifying essential services are still running..."
for svc in ssh NetworkManager ufw cron rsyslog; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        echo "  ✓ $svc is running"
    else
        echo "  ✗ $svc is NOT running — check manually"
    fi
done

echo ""
echo "==> Cleanup complete. Recommended: reboot the server."
echo "    sudo reboot"
