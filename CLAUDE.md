# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the WG_UFW Manager (interactive CLI)
python wg_ufw_manager.py

# Run status check
python wg_ufw_manager.py --status

# Run with AI assistant mode
python wg_ufw_manager.py --ai
```

### Deployment scripts (never run sudo manually — use these scripts)
```bash
bash scripts/install.sh              # Install WireGuard + UFW on Ubuntu 24.04
bash scripts/configure-server.sh     # Generate keys + create wg0.conf
bash scripts/add-client.sh <name>    # Add a new peer/client
bash scripts/remove-client.sh <name> # Remove a peer/client
bash scripts/ufw-rules.sh            # Apply UFW rules for WireGuard
bash scripts/start-wg.sh             # Start WireGuard interface
bash scripts/stop-wg.sh              # Stop WireGuard interface
bash scripts/status.sh               # Show WireGuard + UFW status
bash scripts/backup.sh               # Backup WireGuard config
```

## Architecture

WG_UFW-Server is a WireGuard VPN + UFW firewall management tool for Ubuntu 24.04 with an optional Claude AI assistant interface.

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
