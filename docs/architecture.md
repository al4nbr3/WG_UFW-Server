# Architecture

WG-home-VPN is a single-host WireGuard VPN gateway with UFW as the policy layer.
Everything lives on **`.195`** (V10L3T4): the WireGuard kernel interface, the UFW
rules that filter what can reach it and where its traffic can go, and the
`wg_ufw_manager.py` CLI that drives both.

## Hosts

| Host  | IP              | Role                  | Services                                                  |
|-------|-----------------|-----------------------|-----------------------------------------------------------|
| `.195`| `192.168.1.195` | Gateway (V10L3T4)     | `wg-quick@wg0` (`443/udp`), UFW, sshd                     |
| Peers | `10.0.0.2…4`    | WireGuard clients     | WireGuard tunnel; LAN reachable via `wg0`                 |

The same host also runs Tor (`9050`) and Privoxy (`8118`) for the **cadena-prox**
project — see [`cadena-prox/docs/architecture.md`](https://github.com/al4nbr3/cadena-prox)
for the Tor data plane. This document covers the WireGuard + UFW layer only.

## Data plane — peer to internet

```
  WG client (e.g. 10.0.0.4)                       Gateway .195 (V10L3T4)
 ┌─────────────────────────┐                     ┌────────────────────────────────────┐
 │  WireGuard client       │                     │ UFW input:                         │
 │  PrivateKey + PSK       │  encrypted UDP/443  │   ALLOW 443/udp from Anywhere      │
 │  AllowedIPs = 0.0.0.0/0 │ ───────────────────▶│            │                       │
 │  Endpoint = .195:443    │                     │            ▼                       │
 └─────────────────────────┘                     │   wg-quick@wg0 (kernel)            │
                                                 │   decrypt + identify peer by key   │
                                                 │            │                       │
                                                 │            ▼                       │
                                                 │   wg0 interface (10.0.0.1/24)      │
                                                 │            │                       │
                                                 │            ▼                       │
                                                 │ UFW forward (added by PostUp):     │
                                                 │   ALLOW FWD in:wg0 out:enp0s31f6   │
                                                 │            │                       │
                                                 │            ▼                       │
                                                 │ iptables nat POSTROUTING:          │
                                                 │   MASQUERADE -o enp0s31f6          │
                                                 │            │                       │
                                                 └────────────│───────────────────────┘
                                                              ▼
                                                  enp0s31f6 → 192.168.1.1 (router) → internet
```

Key points:

- **Identity is the public key, not the IP.** The client's external IP can change
  freely (mobile, NAT, ISP rotation); WireGuard rebinds the peer on each handshake
  ("roaming"). The fixed value is `AllowedIPs` inside the tunnel.
- **No DNS leak through the gateway itself.** Egress is plain NAT — the client's
  resolver setting (`DNS = 1.1.1.1, 8.8.8.8` in the client config) is what's used.
  If you want DNS through Tor, route the client's HTTP through Privoxy on the same
  host (cadena-prox flow).
- **The PostUp hooks make UFW and the routing table consistent.** Without them,
  packets would arrive at `wg0` but UFW's `default deny forward` would drop them.

## Control plane — how config lands on the wire

```
 Operator workstation (any host)                     Gateway .195
 ┌──────────────────────────────────┐               ┌────────────────────────────────┐
 │ git clone WG-home-VPN            │               │ /opt/WG_UFW-Server             │
 │   │                              │               │   ├── wg_ufw_manager.py        │
 │   ▼                              │  rsync/SSH    │   ├── lib/wireguard.py         │
 │ scripts/deploy.sh ───────────────┼──────────────▶│   ├── lib/ufw.py               │
 │                                  │               │   └── scripts/                 │
 └──────────────────────────────────┘               │         │                      │
                                                    │         ▼ (run on host)        │
                                                    │   scripts/install.sh           │
                                                    │   scripts/configure-server.sh  │
                                                    │   scripts/ufw-rules.sh         │
                                                    │   scripts/add-client.sh        │
                                                    │   scripts/sync-config.sh       │
                                                    │         │                      │
                                                    │         ▼                      │
                                                    │   /etc/wireguard/wg0.conf      │
                                                    │   /etc/ufw/* (rules)           │
                                                    │   wg-quick@wg0 (systemd)       │
                                                    └────────────────────────────────┘
```

Notes:

- `deploy.sh` is the **only** local-machine script — everything else runs on the
  gateway. The project rule is "never run sudo manually" — the host-side scripts
  call `sudo` internally so the operator just runs `bash scripts/<name>.sh`.
- `wg_ufw_manager.py` is the single CLI entry point — it reads/writes
  `wg0.conf`, generates client config files, and dispatches to the bash scripts
  in `scripts/` for privileged operations.
- `sync-config.sh` is the safe way to apply edits to a live `wg0.conf` —
  it uses `wg syncconf` so the running interface picks up changes without
  going down. Restarting `wg-quick@wg0` would, with `SaveConfig = true`,
  overwrite manual edits with the runtime state on the way down.

## UFW rule structure

Three layers stack to produce the policy:

| Source of rule | Lifetime | Examples |
|----------------|----------|----------|
| `scripts/ufw-rules.sh` (static, applied once) | Persistent across reboots | `ALLOW 443/udp`, `ALLOW OpenSSH`, `ALLOW 10.0.0.0/24 from 10.0.0.0/24`, `ALLOW 192.168.1.0/24 ↔ 10.0.0.0/24` |
| `wg0.conf` `PostUp` (dynamic, every interface up) | Lives only while `wg0` is up | `ufw route allow in on wg0 out on enp0s31f6` |
| `wg0.conf` `PreDown` (dynamic, every interface down) | Removes the PostUp rule | inverse of the above |

The split matters: the static rules don't depend on `wg0` being up (so SSH and
LAN access keep working even with WireGuard down), and the forward rules
auto-adjust if `wg0` is renamed or the upstream interface changes.

## Peers

| Tunnel IP | Notes (as of 2026-04-30)                |
|-----------|------------------------------------------|
| `10.0.0.1/24` | Server (`wg0` itself)                |
| `10.0.0.2/32` | LAN client (Windows — `p0rk3y`)      |
| `10.0.0.3/32` | LAN client                           |
| `10.0.0.4/32` | Remote/WAN client (roaming)          |

Each peer entry in `wg0.conf` has a `PublicKey`, `PresharedKey`, and `AllowedIPs`.
The `Endpoint` line is the **last seen** address of the peer — it auto-updates on
each handshake, so it's not a stable identifier and shouldn't be relied on.

## Security boundaries

| Boundary                                | Enforcement                                                               |
|-----------------------------------------|---------------------------------------------------------------------------|
| Internet → WireGuard handshake          | UFW `ALLOW 443/udp` (must be open — that's the front door)                |
| Internet → SSH                          | UFW `ALLOW OpenSSH` (consider scoping to LAN or a jump host)              |
| Internet → other host services          | Default deny (UFW `default deny incoming`)                                |
| LAN → WG subnet (`10.0.0.0/24`)         | UFW `ALLOW 10.0.0.0/24 from 192.168.1.0/24`                               |
| WG → LAN (`192.168.1.0/24`)             | UFW `ALLOW 192.168.1.0/24 from 10.0.0.0/24`                               |
| WG → internet                           | UFW route `wg0 → enp0s31f6` + iptables MASQUERADE (PostUp)                |
| Peer ↔ peer authentication              | WireGuard public key + per-peer `PresharedKey` (post-quantum belt)        |
| Config file readable by non-root        | `/etc/wireguard/wg0.conf` mode `600`, owner `root`                        |
| Client private keys in git              | `.gitignore` excludes `config/clients/`, `*.key`, `.env`                  |

## Known non-goals

- **Not** a hidden-service host — Tor + Privoxy on the same machine belong to the
  cadena-prox project; this project is just the VPN/firewall layer.
- **Not** multi-user — there's no per-peer auth beyond the shared trust of the
  server pubkey + per-peer PSK; revocation = remove the peer block + reload.
- **Not** HA — `wg-quick@wg0` is a single systemd unit on a single host; if `.195`
  is down, all peers are offline.
- **Not** managing the upstream router — the `443/udp` port-forward on the
  Verizon CR1000B is configured manually and tracked in
  `project_wg_ufw` notes.
