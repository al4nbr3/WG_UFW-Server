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
- [x] `scripts/deploy.sh` — Deploy project to remote via rsync/SSH
- [x] `scripts/cleanup-server.sh` — Remove non-essential services/packages
- [x] `config/wg0.conf.template` — WireGuard config template
- [x] `docs/SETUP.md` — Full setup and usage documentation
- [x] GitHub repo created and pushed (`al4nbr3/WG_UFW-Server`)

## Session: 2026-03-15 — Remote Deployment & First Client

### Completed
- [x] SSH enabled on remote server `192.168.1.195` (user: `observa`, hostname: `V10L3T4`)
- [x] Remote specs confirmed: 15 GB RAM, 234 GB NVMe, 8-core Intel i7-7700T
- [x] `scripts/cleanup-server.sh` ran — removed logstash, suricata, snort, samba, cups, bluetooth, browsers, VirtualBox
- [x] `scripts/deploy.sh` fixed — added `ssh -t` flag for sudo TTY
- [x] `scripts/add-client.sh` fixed — replaced process substitution with tmpfile for preshared key
- [x] Remote deployed to `/opt/WG_UFW-Server`
- [x] WireGuard installed and running on `enp0s31f6` interface, IP `10.0.0.1/24`
- [x] UFW configured — port `51820/udp` open, SSH preserved
- [x] `wg-quick@wg0` enabled on boot
- [x] Client `p0rk3y` (Windows PC) created — IP `10.0.0.2/32`
- [x] `.env` configured on remote with `ANTHROPIC_API_KEY`
- [x] Python dependencies installed on remote

### In Progress
- [ ] Transfer `p0rk3y.conf` to Windows machine and import into WireGuard app

### Pending
- [ ] Verify WireGuard tunnel works from p0rk3y (Windows) to server
- [ ] Add client QR code generation for mobile devices
- [ ] Add DNS leak test script
- [ ] Add monitoring/status web dashboard
- [ ] Add auto-renewal for IP forwarding on kernel updates

## Session: 2026-04-30 — Configuration Audit (WG + Tor + Privoxy)

### Verified live state on V10L3T4 (192.168.1.195)
- [x] WireGuard `wg-quick@wg0` enabled + active
- [x] WireGuard listen port confirmed as **`443/udp`** (changed from documented `51820/udp`)
- [x] 3 peers active on wg0: `10.0.0.2/32`, `10.0.0.3/32`, `10.0.0.4/32`
- [x] PostUp/PreDown hooks use full path `/usr/sbin/ufw` (avoids PATH issues under wg-quick)
- [x] `iptables MASQUERADE` on `enp0s31f6` for outbound NAT
- [x] `net.ipv4.ip_forward = 1`
- [x] Tor service enabled + active — SocksPort on `127.0.0.1:9050` and `192.168.1.195:9050`
- [x] Tor SocksPolicy restricts SOCKS to localhost + `192.168.1.0/24`
- [x] Tor Hidden Service configured (`/var/lib/tor/hidden_service/`, port 80 → `127.0.0.1:8080`)
- [x] Privoxy enabled + active — listens on lo + `192.168.1.195:8118`
- [x] Privoxy chains all HTTP through Tor (`forward-socks5t / 127.0.0.1:9050 .`)
- [x] UFW exposes `9050/tcp` and `8118/tcp` to LAN only

### Completed
- [x] Stripped stale `Endpoint =` lines from `/etc/wireguard/wg0.conf` peer blocks
- [x] Created `docs/CURRENT-CONFIG.md` — single source of truth for live deployment state
- [x] Created `scripts/sync-config.sh` — apply `wg0.conf` edits live via `wg syncconf` without bouncing the interface
- [x] Created `scripts/audit-server.sh` — one-shot audit of WG + Tor + Privoxy + UFW
- [x] Patched `config/wg0.conf.template` — full path `/usr/sbin/ufw` in PostUp/PreDown
- [x] Patched `docs/SETUP.md` — added pointer to `CURRENT-CONFIG.md` and a Tor + Privoxy section
- [x] Patched `CLAUDE.md` — port now `443/udp`, registered clients table updated to 3 peers
- [x] Removed stray `192.168.1.9` file (nmap output left from a typo'd `-o` flag)

### Pending
- [ ] Decide whether to flip `SaveConfig = true` → `false` (avoids wg-quick rewriting the file on stop)
- [ ] Remove stale UFW rule `51820/udp ALLOW Anywhere` (no longer in use)
- [ ] Review whether `5601/tcp` (Kibana) and `9200/tcp` (Elasticsearch) should be LAN-scoped instead of Anywhere
- [ ] Add a DDNS hostname for the server's public IP and use it in client `Endpoint =`
- [ ] Update `lib/wireguard.py` and `wg_ufw_manager.py` defaults to `443/udp` for new deployments

## Session: 2026-04-30 — Architecture Documentation

### Completed
- [x] Created `docs/architecture.md` — data plane (peer → wg0 → MASQUERADE → enp0s31f6), control plane (deploy.sh → CLI → wg-quick), UFW rule structure (static + PostUp dynamic + iptables NAT), peer table, security boundaries, and known non-goals
- [x] Updated `README.md` — added compact Architecture section with ASCII diagram and links to `docs/architecture.md` + `docs/CURRENT-CONFIG.md`
- [x] Style mirrors `cadena-prox/docs/architecture.md` so both projects read consistently when looked at side-by-side

## Session: 2026-04-30 — README cleanup

### Completed
- [x] Removed `sudo` prefix from all script invocations in README (project rule: scripts call sudo internally; users run as normal user)
- [x] Added explicit "Don't prefix with sudo" callout in the Setup section + a note on the Scripts Reference table
- [x] Annotated `WG_PORT=51820` in the env example as the default; noted production V10L3T4 uses 443
- [x] Added `sync-config.sh` and `audit-server.sh` to the Scripts Reference table with their own usage subsections
- [x] Fixed `cleanup-server.sh` description — was "Removes WireGuard and resets UFW" (wrong); now reflects "removes non-essential packages, leaves WG+UFW intact"
- [x] Sharpened other Scripts Reference descriptions (e.g. `start-wg.sh` notes the systemd enable; `add-client.sh` notes both wg0.conf edit and client config generation)
