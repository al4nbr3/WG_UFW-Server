# Current Server Configuration — V10L3T4

Live state of services on `observa@192.168.1.195` as of **2026-04-30**.
Generated from a direct audit of the running system. Secrets (private keys,
preshared keys, the `.onion` hostname) are intentionally redacted — see the
live files on the remote for those values.

---

## Host

| Item | Value |
|------|-------|
| Hostname | `V10L3T4` |
| LAN IP | `192.168.1.195` |
| **Public WAN IP** | **`173.72.152.119`** (Verizon FIOS, **static** — no DDNS required) |
| Kernel | `6.8.0-110-generic` (Ubuntu) |
| Default interface | `enp0s31f6` |
| Deployed project path | `/opt/WG_UFW-Server` |

Reverse DNS: `pool-173-72-152-119.clppva.fios.verizon.net`. Confirmed static
2026-05-01.

### Upstream router (Verizon CR1000B at `192.168.1.1`)

| Forward | Status |
|---------|--------|
| `UDP/443 → 192.168.1.195:443` | **Required** for off-LAN WireGuard handshakes (Slot C / cellular). Currently working as of 2026-05-01 (handshake from AT&T Mi-Fi WAN confirmed). |
| `UDP/51820 → 192.168.1.195` | **Legacy** — was used before WG moved to 443/udp. Safe to remove from the router. |

---

## WireGuard

| Item | Value |
|------|-------|
| Service | `wg-quick@wg0` — enabled, active |
| Interface | `wg0` — `10.0.0.1/24` |
| Listen port | **`443/udp`** (changed from default 51820 to look like HTTPS) |
| Config file | `/etc/wireguard/wg0.conf` (root, mode 600) |
| `SaveConfig` | `true` — wg-quick rewrites the file on stop |

### PostUp / PreDown hooks

```ini
PostUp  = /usr/sbin/ufw route allow in on wg0 out on enp0s31f6
PostUp  = iptables -t nat -I POSTROUTING -o enp0s31f6 -j MASQUERADE
PreDown = /usr/sbin/ufw route delete allow in on wg0 out on enp0s31f6
PreDown = iptables -t nat -D POSTROUTING -o enp0s31f6 -j MASQUERADE
```

### Peers

| Tunnel IP | Public key (truncated) | Role | Notes |
|-----------|------------------------|------|-------|
| `10.0.0.2/32` | `IDkYO+1b…` | (orphan) | Slot exists but no client `.conf` was deployed to a device. Safe to remove. |
| `10.0.0.3/32` | `2FhYqmqv…` | **Slot B — LAN endpoint** | p0rk3y (Windows) when at home. Client `Endpoint = 192.168.1.195:443`. Verified handshake 2026-05-01. |
| `10.0.0.4/32` | `dulWIAN6…` | **Slot C — WAN endpoint** | p0rk3y (Windows) when off-LAN (cellular/remote). Client `Endpoint = 173.72.152.119:443`. Requires `MTU = 1280` for cellular paths. Verified handshake 2026-05-01 from AT&T Mi-Fi (cellular IP `107.121.104.39`). |

All three peers use a `PresharedKey`. Full keys live in `/etc/wireguard/wg0.conf`
on the server (root-only) — never copy them into this repo.

### Reloading after edits

`SaveConfig = true` overwrites the file on `systemctl restart wg-quick@wg0`,
which destroys manual edits. Use `bash scripts/sync-config.sh` instead — it
applies file changes to the running interface in place via `wg syncconf`.

---

## Tor

| Item | Value |
|------|-------|
| Service | `tor` — enabled, active |
| Config file | `/etc/tor/torrc` |
| Data dir | `/var/lib/tor/` |

### Active directives

```text
SocksPort     127.0.0.1:9050
SocksPort     192.168.1.195:9050
SocksPolicy   accept 127.0.0.1
SocksPolicy   accept 192.168.1.0/24
SocksPolicy   reject *

HiddenServiceDir   /var/lib/tor/hidden_service/
HiddenServicePort  80 127.0.0.1:8080
```

The `.onion` hostname for the hidden service is in
`/var/lib/tor/hidden_service/hostname` on the server. **Treat it as a secret —
do not commit it to this repo, even though the repo is private.**

---

## Privoxy

| Item | Value |
|------|-------|
| Service | `privoxy` — enabled, active |
| Config file | `/etc/privoxy/config` |
| Listen | `127.0.0.1:8118`, `[::1]:8118`, `192.168.1.195:8118` |
| Forward chain | `forward-socks5t / 127.0.0.1:9050 .` (all HTTP through Tor) |

Privoxy gives LAN clients an HTTP proxy front-end onto Tor:
LAN browser → `192.168.1.195:8118` → Tor SOCKS5 (`127.0.0.1:9050`) → exit relay.

---

## UFW

```
22/tcp                       ALLOW   Anywhere
OpenSSH                      ALLOW   Anywhere
3389/tcp                     ALLOW   192.168.1.0/24            # RDP, LAN only
3389/tcp                     ALLOW   192.168.1.243
443/udp                      ALLOW   Anywhere                  # WireGuard
51820/udp                    ALLOW   Anywhere                  # legacy WG port — review
5601/tcp                     ALLOW   Anywhere                  # Kibana — review
9200/tcp                     ALLOW   Anywhere                  # Elasticsearch — review
9050/tcp                     ALLOW   192.168.1.0/24            # Tor SOCKS5 (LAN only)
8118/tcp                     ALLOW   192.168.1.0/24            # Privoxy HTTP (LAN only)
10.0.0.0/24                  ALLOW   10.0.0.0/24
10.0.0.0/24                  ALLOW   192.168.1.0/24
192.168.1.0/24               ALLOW   10.0.0.0/24

192.168.1.0/24 on enp0s31f6  ALLOW FWD  Anywhere on wg0
Anywhere on enp0s31f6        ALLOW FWD  Anywhere on wg0
```

`net.ipv4.ip_forward = 1`.

### Items to review

- `51820/udp` is open but no longer in use (WireGuard moved to 443/udp) — candidate for removal.
- `5601/tcp` (Kibana) and `9200/tcp` (Elasticsearch) are open to **Anywhere**. If these
  services aren't intended to be internet-reachable, scope them to `192.168.1.0/24`.

---

## Quick reference

| Task | Command (run on the server) |
|------|-----------------------------|
| Snapshot full state | `bash scripts/audit-server.sh` |
| Apply edited `wg0.conf` without bouncing the interface | `bash scripts/sync-config.sh` |
| WireGuard status | `bash scripts/status.sh` |
| Tor service status | `systemctl status tor` |
| Privoxy service status | `systemctl status privoxy` |

---

## Source of truth

- This document is generated from a live audit. Re-run `bash scripts/audit-server.sh`
  on the remote before treating any value here as still current.
- The `cadena-prox` project (separate private repo) owns the operational portal that
  monitors this server — see that repo for portal/SSH-monitor specifics.
