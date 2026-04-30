# WG_UFW-Server

WireGuard VPN + UFW Firewall manager for Ubuntu 24.04 with an optional Claude AI assistant for troubleshooting and guidance.

## Features

- Full WireGuard VPN server setup and client management
- UFW firewall rules configuration
- Add, remove, and list VPN clients
- Start/stop WireGuard interface
- Server status dashboard (Rich terminal UI)
- Backup and cleanup scripts
- Optional Claude AI assistant for help and diagnostics

## Architecture

```
 WG client (10.0.0.x)                   Gateway (.195, V10L3T4)
 ┌─────────────────┐                    ┌──────────────────────────────────┐
 │ WireGuard peer  │   UDP/443 (encrypted)   UFW input: ALLOW 443/udp     │
 │ AllowedIPs      │ ──────────────────▶│  wg-quick@wg0 ── wg0 (10.0.0.1) │
 │   = 0.0.0.0/0   │                    │       │                          │
 └─────────────────┘                    │       ▼                          │
                                        │  UFW forward (PostUp hook):      │
                                        │   ALLOW FWD wg0 → enp0s31f6      │
                                        │       │                          │
                                        │       ▼                          │
                                        │  iptables MASQUERADE             │
                                        │   on enp0s31f6                   │
                                        └───────│──────────────────────────┘
                                                ▼
                                          internet (via 192.168.1.1)
```

UFW policy comes from three layers: static rules from `scripts/ufw-rules.sh`,
dynamic per-interface rules added by `wg0.conf`'s `PostUp` / `PreDown` hooks,
and `iptables` NAT for masquerading. See [`docs/architecture.md`](docs/architecture.md)
for the full data-plane diagram, control-plane (deploy → CLI → wg-quick),
peer table, and security boundaries.

For the live state of the production server (port, peers, UFW rules),
see [`docs/CURRENT-CONFIG.md`](docs/CURRENT-CONFIG.md).

## Requirements

- Ubuntu 24.04 server
- Python 3.11+
- Root/sudo access
- Anthropic API key (optional, for AI assistant)

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/al4nbr3/WG_UFW-Server.git
cd WG_UFW-Server
```

**2. Create and activate a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**3. Configure environment variables**

```bash
cp .env.example .env
nano .env
```

Set the following values:

```env
SERVER_PUBLIC_IP=your.server.ip
WG_PORT=51820                     # default; production V10L3T4 uses 443 instead
WG_SERVER_IP=10.0.0.1
WG_DNS=1.1.1.1, 8.8.8.8
ANTHROPIC_API_KEY=your_key_here   # optional
```

> Don't prefix any of the scripts below with `sudo` — they call `sudo` internally
> for the bits that need it. Run them as your normal user.

**4. Run the server setup scripts**

```bash
bash scripts/install.sh
bash scripts/configure-server.sh
```

**5. Apply UFW firewall rules**

```bash
bash scripts/ufw-rules.sh
```

**6. Start WireGuard**

```bash
bash scripts/start-wg.sh
```

## Usage

### Check Status

```bash
python wg_ufw_manager.py --status
```

### List Clients

```bash
python wg_ufw_manager.py --list-clients
```

### Add a Client

```bash
python wg_ufw_manager.py --add-client clientname
```

A `.conf` file will be generated — share it with the client device.

### Remove a Client

```bash
bash scripts/remove-client.sh clientname
```

### Stop WireGuard

```bash
bash scripts/stop-wg.sh
```

### Backup Configuration

```bash
bash scripts/backup.sh
```

### Apply edited `wg0.conf` without bouncing the interface

```bash
bash scripts/sync-config.sh
```

Use this after editing `/etc/wireguard/wg0.conf` by hand. It calls
`wg syncconf` so the running peers stay connected. Restarting `wg-quick@wg0`
would, with `SaveConfig = true`, overwrite manual edits with runtime state.

### Snapshot full server state

```bash
bash scripts/audit-server.sh
```

Prints WireGuard, Tor, Privoxy, UFW, and routing state in one shot.

### Strip non-essential services / packages

```bash
bash scripts/cleanup-server.sh
```

Removes packages this VPN box doesn't need (logstash, suricata, snort,
samba, cups, bluetooth, browsers, VirtualBox, etc.) — does **not** remove
WireGuard or UFW.

## AI Assistant

If `ANTHROPIC_API_KEY` is set in `.env`, you can ask the AI assistant for help:

```bash
python wg_ufw_manager.py --ask "How do I add a client for a mobile device?"
```

## Scripts Reference

All scripts call `sudo` internally where needed — run them as your normal user.

| Script | Description |
|--------|-------------|
| `install.sh` | Installs WireGuard, UFW, and dependencies |
| `configure-server.sh` | Generates server keys and writes `/etc/wireguard/wg0.conf` |
| `ufw-rules.sh` | Applies the static UFW rule set for the VPN |
| `start-wg.sh` | Brings up `wg-quick@wg0` and enables it on boot |
| `stop-wg.sh` | Stops the WireGuard interface |
| `add-client.sh` | Adds a new VPN peer (writes `wg0.conf` + generates client config) |
| `remove-client.sh` | Removes a VPN peer |
| `status.sh` | Shows WireGuard + UFW + systemd status |
| `sync-config.sh` | Applies `/etc/wireguard/wg0.conf` edits to the live interface via `wg syncconf` (no bounce) |
| `audit-server.sh` | One-shot snapshot of WireGuard, Tor, Privoxy, UFW, and routing |
| `backup.sh` | Backs up server configuration |
| `cleanup-server.sh` | Removes non-essential packages (browsers, samba, cups, etc.) — leaves WireGuard + UFW intact |
| `deploy.sh` | rsync-over-SSH deploy from a workstation to the gateway |
