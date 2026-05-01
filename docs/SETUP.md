# WG_UFW-Server Setup Guide

WireGuard VPN + UFW Firewall on Ubuntu 24.04 with Claude AI assistant.

> **Looking for the live state of the production server (V10L3T4)?**
> See [`CURRENT-CONFIG.md`](CURRENT-CONFIG.md). This guide describes a
> fresh install using project defaults; the production deployment overrides
> a few values (e.g. WireGuard listens on `443/udp` instead of `51820/udp`,
> and Tor + Privoxy are also installed alongside).

---

## Requirements

| Item | Details |
|------|---------|
| OS | Ubuntu 24.04 LTS |
| RAM | 512 MB minimum, 1 GB recommended |
| Disk | 5 GB minimum |
| Python | 3.10+ |
| Network | Static IP or DDNS on the server |

---

## Step 1 — Clone the project

```bash
git clone https://github.com/al4nbr3/WG-home-VPN.git
cd WG-home-VPN
```

---

## Step 2 — Set up environment

```bash
cp .env.example .env
nano .env
```

Set your `ANTHROPIC_API_KEY` if you want the AI assistant. All other values have safe defaults.

---

## Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## Step 4 — Install WireGuard + UFW on the server

```bash
bash scripts/install.sh
```

This installs `wireguard` and `ufw` via apt and enables IP forwarding in `/etc/sysctl.conf`.

---

## Step 5 — Configure the WireGuard server

```bash
bash scripts/configure-server.sh
```

This:
- Generates a server private/public key pair
- Writes `/etc/wireguard/wg0.conf` (permissions 600)
- Saves the public key to `config/server_public.key`
- Detects your primary network interface automatically

---

## Step 6 — Apply UFW firewall rules

```bash
bash scripts/ufw-rules.sh
```

Rules applied:
- `51820/udp` — WireGuard tunnel
- `OpenSSH` — SSH access (keeps you from getting locked out)
- Route traffic from `wg0` to your network interface

---

## Step 7 — Start WireGuard

```bash
bash scripts/start-wg.sh
```

Enables `wg-quick@wg0` as a systemd service (starts on boot).

---

## Step 8 — Add a client (peer)

```bash
# Generate client config
python wg_ufw_manager.py --add-client laptop

# Apply to live server
bash scripts/add-client.sh laptop
```

Client config is saved to `config/clients/laptop.conf`.
Copy this file to your device or use a QR code app to import it.

---

## Step 9 — Verify

```bash
bash scripts/status.sh
```

Or via the Python manager:

```bash
python wg_ufw_manager.py --status
```

---

## Day-to-Day Commands

| Task | Command |
|------|---------|
| Check status | `bash scripts/status.sh` |
| Add a client | `python wg_ufw_manager.py --add-client <name>` then `bash scripts/add-client.sh <name>` |
| Remove a client | `python wg_ufw_manager.py --remove-client <name>` then `bash scripts/remove-client.sh <name>` |
| List all clients | `python wg_ufw_manager.py --list-clients` |
| Backup config | `bash scripts/backup.sh` |
| Stop WireGuard | `bash scripts/stop-wg.sh` |
| AI assistant | `python wg_ufw_manager.py --ai` |

---

## AI Assistant

If `ANTHROPIC_API_KEY` is set in `.env`, the AI assistant mode provides interactive
guidance for setup, troubleshooting, and UFW rule changes:

```bash
python wg_ufw_manager.py --ai
```

Type your question at the prompt. The assistant is aware of WireGuard and UFW
on Ubuntu 24.04. Type `exit` to quit.

---

## Client Configuration (example)

After running `--add-client`, the file `config/clients/<name>.conf` looks like:

```ini
[Interface]
PrivateKey = <CLIENT_PRIVATE_KEY>
Address = 10.0.0.2/32
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = <SERVER_PUBLIC_KEY>
PresharedKey = <PRESHARED_KEY>
Endpoint = YOUR.SERVER.IP:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```

Import this file into:
- **Linux**: `sudo wg-quick up /path/to/name.conf`
- **Windows/macOS**: WireGuard app → Import tunnel
- **Android/iOS**: WireGuard app → scan QR code

---

## UFW + WireGuard — How It Works

```
Client → Internet → Server:51820/udp (UFW allows)
                        ↓
                   WireGuard decrypts
                        ↓
                   wg0 interface (10.0.0.x)
                        ↓
              UFW routes wg0 → eth0
                        ↓
              iptables MASQUERADE → Internet
```

The `PostUp`/`PreDown` hooks in `wg0.conf` handle routing and NAT automatically
when the WireGuard interface comes up or goes down.

---

## Security Notes

- Private keys are stored in `/etc/wireguard/wg0.conf` (root-only, mode 600)
- Client private keys are generated locally and saved to `config/clients/<name>.conf` — **never committed to git**
- The `.gitignore` excludes all `*.key`, `.env`, and `config/clients/` files
- Preshared keys (PSK) add a layer of post-quantum resistance between each peer pair

---

## Tor + Privoxy (V10L3T4 deployment)

The production server also runs **Tor** and **Privoxy** for LAN clients that
want to route HTTP traffic through Tor. These aren't part of a fresh install
of this project — they were configured separately on V10L3T4. For the live
config (ports, SocksPolicy, hidden service, forward chain), see
[`CURRENT-CONFIG.md`](CURRENT-CONFIG.md).

LAN usage from any client on `192.168.1.0/24`:

| Proxy type | Address |
|------------|---------|
| HTTP (via Privoxy → Tor) | `192.168.1.195:8118` |
| SOCKS5 (direct to Tor) | `192.168.1.195:9050` |

UFW already restricts both ports to `192.168.1.0/24`. Do **not** open them
to `Anywhere`.

---

## Troubleshooting

| Issue | Check |
|-------|-------|
| Can't connect | `bash scripts/status.sh` — verify wg0 is up and peer is listed |
| No internet on client | Check IP forwarding: `cat /proc/sys/net/ipv4/ip_forward` (must be 1) |
| UFW blocking | `sudo ufw status verbose` — confirm 51820/udp is ALLOW |
| SSH locked out | Make sure `ufw allow OpenSSH` ran before enabling UFW |
| Wrong interface | Check `ip route` — the interface in `wg0.conf` must match your default route |
