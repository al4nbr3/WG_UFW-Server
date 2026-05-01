# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WG_UFW-Server manages a WireGuard VPN + UFW firewall on Ubuntu 24.04. The server is deployed at:
- **Remote server:** `192.168.1.195` (hostname: `V10L3T4`, user: `observa`)
- **Deployed path:** `/opt/WG_UFW-Server`
- **WireGuard interface:** `wg0` on `enp0s31f6`, server IP `10.0.0.1/24`
- **WireGuard port:** `443/udp` on V10L3T4 (default for new installs is still `51820/udp`)
- **GitHub repo:** `https://github.com/al4nbr3/WG-home-VPN` (private; renamed 2026-05-01 from `WG_UFW-Server`)

The server also runs **Tor** (`SocksPort 9050`, LAN-scoped) and **Privoxy**
(`8118`, chains HTTP through Tor) — see `docs/CURRENT-CONFIG.md`.

## Registered Clients

| Name | IP | Device |
|------|----|--------|
| p0rk3y | 10.0.0.2/32 | Windows PC |
| (peer-3) | 10.0.0.3/32 | LAN client |
| (peer-4) | 10.0.0.4/32 | Remote/WAN client |

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the WG_UFW Manager (interactive CLI)
python wg_ufw_manager.py

# Run status check
python wg_ufw_manager.py --status

# List clients
python wg_ufw_manager.py --list-clients

# Add a client
python wg_ufw_manager.py --add-client <name>

# Run with AI assistant mode
python wg_ufw_manager.py --ai
```

### Deployment scripts (never run sudo manually — use these scripts)
```bash
bash scripts/deploy.sh               # Deploy from local machine to 192.168.1.195
bash scripts/install.sh              # Install WireGuard + UFW on Ubuntu 24.04
bash scripts/configure-server.sh     # Generate keys + create wg0.conf
bash scripts/add-client.sh <name>    # Add a new peer/client
bash scripts/remove-client.sh <name> # Remove a peer/client
bash scripts/ufw-rules.sh            # Apply UFW rules for WireGuard
bash scripts/start-wg.sh             # Start WireGuard interface
bash scripts/stop-wg.sh              # Stop WireGuard interface
bash scripts/status.sh               # Show WireGuard + UFW status
bash scripts/backup.sh               # Backup WireGuard config
bash scripts/cleanup-server.sh       # Remove non-essential services/packages
bash scripts/sync-config.sh          # Apply edits in /etc/wireguard/wg0.conf live
bash scripts/audit-server.sh         # Snapshot WG + Tor + Privoxy + UFW state
```

## Architecture

```
wg_ufw_manager.py (CLI entry point)
    ├── lib/wireguard.py     → WireGuard key gen, peer management, config I/O
    ├── lib/ufw.py           → UFW rule generation and application
    ├── lib/ai_assistant.py  → Claude API integration for guided setup/troubleshooting
    └── scripts/             → Privileged bash scripts (all sudo operations here)
```

## Coding Style

- **Comments**: sparingly. Only comment genuinely non-obvious logic.
- **Credentials**: never hardcode API keys, tokens, or secrets. Always load from `.env` or env vars.
- **sudo**: NEVER ask the user to run sudo manually. Write a `scripts/` bash script instead.

## Workflow Preferences

- Before proposing changes, check `CHECKLIST.md` to understand what already exists.
- **CHECKLIST.md auto-update**: After EVERY change (code, scripts, config, fixes), immediately update `CHECKLIST.md`.
- **Change confirmation**: After any file(s) are modified, always end with a summary block listing every file updated, created, or deleted — with ✅ confirmation.

## API Keys

- `ANTHROPIC_API_KEY` — Claude AI assistant features (optional; falls back to manual mode if not set)
- Loaded from `.env` file at project root (never committed to git)
- `.env` is configured on the remote server at `/opt/WG_UFW-Server/.env`

## Resuming Work

To continue working on this project in a new session:
1. Open Claude Code from any machine
2. `cd /mnt/jbaez_data/Scripts-linux/WG_UFW-Server`
3. Read `CHECKLIST.md` to see current state and pending tasks
4. SSH into remote: `ssh observa@192.168.1.195`
