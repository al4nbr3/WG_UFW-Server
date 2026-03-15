# CHECKLIST.md — WG_UFW-Server

## Session: 2026-03-14 — Initial Project Setup

### Completed
- [x] Project scaffold created (`WG_UFW-Server/`)
- [x] `CLAUDE.md` — guidance for Claude Code
- [x] `CHECKLIST.md` — this file
- [x] `.env.example` — API key template
- [x] `.gitignore` — excludes secrets and build artifacts
- [x] `requirements.txt` — Python dependencies
- [x] `wg_ufw_manager.py` — main CLI manager with Claude AI assistant
- [x] `lib/wireguard.py` — WireGuard key generation and peer management
- [x] `lib/ufw.py` — UFW rule management
- [x] `lib/ai_assistant.py` — Claude API integration
- [x] `scripts/install.sh` — Install WireGuard + UFW
- [x] `scripts/configure-server.sh` — Server key gen + wg0.conf
- [x] `scripts/add-client.sh` — Add a WireGuard peer
- [x] `scripts/remove-client.sh` — Remove a WireGuard peer
- [x] `scripts/ufw-rules.sh` — Apply UFW rules
- [x] `scripts/start-wg.sh` — Start WireGuard
- [x] `scripts/stop-wg.sh` — Stop WireGuard
- [x] `scripts/status.sh` — Show WireGuard + UFW status
- [x] `scripts/backup.sh` — Backup config
- [x] `config/wg0.conf.template` — WireGuard config template
- [x] `docs/SETUP.md` — Full setup and usage documentation
- [x] GitHub repo created and pushed (`al4nbr3/WG_UFW-Server`)

### Pending
- [ ] Add client QR code generation for mobile devices
- [ ] Add DNS leak test script
- [ ] Add monitoring/status web dashboard
- [ ] Add auto-renewal for IP forwarding on kernel updates
