# Troubleshooting — WG_UFW-Server

Symptom-first reference for problems encountered (and resolved) when bringing
client tunnels up against `V10L3T4`. If you're reconstructing the project on
a new host or onboarding a new client, check here before the deeper docs.

Each entry is in the form: **Symptom → Diagnosis → Fix → How to verify.**

---

## 1. Client `.conf` ships with the wrong port (`:51820` instead of `:443`)

**Symptom**
- Tunnel shows "Active" in the WireGuard Windows app, but stays at `Transfer: 0 B received`.
- `tcpdump 'udp port 443 or udp port 51820'` on the server captures **zero packets** during a 60-second activation window.
- All other peers also show no `latest handshake:` line in `wg show wg0`.

**Diagnosis**
- The server listens on `443/udp` (chosen to look like HTTPS), but `lib/wireguard.py`
  and `wg_ufw_manager.py` still default to `51820/udp` when generating client configs.
- Result: every client `.conf` produced by `--add-client` has `Endpoint = <ip>:51820`,
  which dials a closed UDP port on the gateway.

**Fix**
- On the client `.conf`, change `Endpoint = <ip>:51820` → `Endpoint = <ip>:443`.
- Permanent fix: update the project defaults so future `--add-client` runs are correct.
  *(Pending in `CHECKLIST.md`.)*

**How to verify**
```bash
# On the gateway, watch for handshake packets while the user activates the tunnel.
sudo tcpdump -i enp0s31f6 -n -tttt -c 20 'udp port 443'
# Then on the gateway:
sudo wg show wg0   # should show "latest handshake: N seconds ago" under the peer
```

---

## 2. Internet goes dark on the client when the tunnel "activates"

**Symptom**
- User clicks **Activate** on a WireGuard tunnel; immediately afterwards the
  client cannot reach **anything** (web pages, internal hosts, DNS).
- The WireGuard app shows the tunnel as Active, but `Received: 0 B`.

**Diagnosis**
- The client `.conf` has `AllowedIPs = 0.0.0.0/0, ::/0`. WireGuard for Windows
  uses this as a **kill switch** — it installs a firewall rule that blocks every
  outbound packet **except those going through the tunnel**.
- When the handshake silently fails (almost always Issue #1 — wrong port), no
  traffic flows through the tunnel either. Net effect: total internet blackout
  while "active."

**Fix — pick the appropriate `AllowedIPs` for the use case**

| Goal | `AllowedIPs` |
|------|--------------|
| Reach LAN hosts only; keep cellular/regular internet on the host network | `10.0.0.0/24, 192.168.1.0/24` (split tunnel — **no kill switch**) |
| Force all traffic through the gateway (e.g., on hostile WiFi) | `0.0.0.0/0, ::/0` (full tunnel — kill switch active) |

For day-to-day cellular use, **split tunnel is the polite choice** — bandwidth
isn't wasted, and a hung handshake doesn't kill all networking.

**How to verify**
- After fixing, re-activate the tunnel. Regular browsing should still work even
  if the handshake hasn't completed (proves split tunnel is in effect).
- `Get-NetRoute` on Windows should show `0.0.0.0/0` still pointing at the LAN gateway,
  not at the WireGuard adapter, when split-tunnel is in use.

---

## 3. NAT hairpinning — Slot C fails when the client is on the LAN

**Symptom**
- Slot C (WAN endpoint, e.g. `Endpoint = 173.72.152.119:443`) doesn't handshake
  when the client is connected to the same home WiFi as the gateway.
- The same Slot C config works fine when the client is off-LAN (cellular).

**Diagnosis**
- LAN client → packet destined for the home WAN IP → home router → packet's destination
  is the router's own WAN address → router needs to "fold" the packet back into the LAN
  to reach `192.168.1.195:443`. This is **NAT hairpinning** (a.k.a. NAT loopback).
- **The Verizon CR1000B does not support NAT hairpinning** (or has it disabled by default).
  Most home routers either don't implement it or disable it.

**Fix**
- Maintain **two tunnels** on devices that move between LAN and WAN:

| Tunnel | `Endpoint =` | Used when… |
|--------|--------------|------------|
| **Slot B** | `192.168.1.195:443` | Connected to home WiFi |
| **Slot C** | `173.72.152.119:443` | On cellular / hotel WiFi / anywhere off-LAN |

- Activate **only one at a time**. Don't both activate at once.

**How to verify**
- On the gateway, `sudo wg show wg0` should show whichever slot is active under
  the connecting client's pubkey, with a recent `latest handshake:` line.
- Activating the *other* slot from the wrong network type produces the same
  "tunnel active, 0 B received" symptom.

---

## 4. SSH and APIs hang/fail over the tunnel from cellular (small things work)

**Symptom**
- Slot C handshake succeeds; `wg show` shows real Tx/Rx volume.
- `ping 192.168.1.180` works fine.
- `ssh user@192.168.1.180` hangs at "Connection established" or after typing the
  password and never proceeds.
- `curl http://192.168.1.180:8090/...` hangs or times out on responses.

**Diagnosis**
- WireGuard's default tunnel MTU is **1420** (1500 − 80 for WG headers).
- Carrier networks (LTE/5G especially AT&T) often have an effective path MTU
  below 1420 once their own encapsulation overhead is added.
- Path MTU Discovery (PMTUD) typically fails because carriers / middleboxes filter
  the ICMP "fragmentation needed" reply.
- Result: small packets (ping, TCP SYN, DNS queries) traverse fine; large packets
  (SSH key exchange, TLS handshakes, API JSON responses) silently disappear.

**Fix**
- On the **client** side, add an `MTU` line to the `[Interface]` block of the
  problematic tunnel:
  ```ini
  [Interface]
  PrivateKey = <existing>
  Address    = 10.0.0.4/32
  DNS        = 1.1.1.1, 8.8.8.8
  MTU        = 1280
  ```
- `1280` is the IPv6 minimum and is safe on essentially every carrier.
- No server-side change is required.

**How to verify**
On the client (Windows command prompt) with the tunnel active:
```cmd
ping -f -l 1252 192.168.1.180     :: should succeed (1252+28 = 1280 — fits)
ping -f -l 1372 192.168.1.180     :: should fail with "Packet needs to be fragmented"
```
After applying `MTU = 1280`, SSH and API calls work.

---

## 5. "Connection refused" when the kill switch is on but tunnel isn't passing data

**Symptom**
- User reports `Connection refused` when trying to reach an internal service
  (e.g., `http://192.168.1.180:8090`) over the tunnel.
- The service IS up — confirmed reachable from the gateway and from other LAN hosts.

**Diagnosis**
- This is *not* a real TCP RST from the destination. It's Windows' Winsock layer
  rejecting the connection because:
  - The kill switch is in effect (`AllowedIPs = 0.0.0.0/0`)
  - The tunnel adapter is "up" but has no working route
  - Windows can't actually deliver the SYN
- Different applications surface this as different errors: "refused", "no route",
  "host unreachable", or just a hang. The underlying cause is the same.

**Fix**
- Resolve the underlying handshake failure (Issues #1, #3, or #4 above).
- Once the handshake completes and traffic flows, "refused" disappears.

**How to verify**
- `wg show wg0` on the gateway must show `latest handshake:` and non-zero
  `transfer:` numbers for the active peer.
- Then re-attempt the connection from the client.

---

## Quick triage cheatsheet

| You see… | Most likely issue |
|----------|-------------------|
| `Transfer: 0 B received`, no handshake on gateway | Wrong port (Issue #1) |
| Internet dies while tunnel "active" | Kill switch + failed handshake (Issue #2) |
| Works on cellular but not at home (or vice versa) | NAT hairpin / wrong endpoint slot (Issue #3) |
| Ping works, SSH/API hangs | MTU (Issue #4) |
| "Connection refused" but service is verified up | Kill switch artifact (Issue #5) |

## Diagnostic commands worth knowing

| Where | Command | Tells you |
|-------|---------|-----------|
| Gateway | `sudo wg show wg0` | Per-peer handshake time and transfer counters |
| Gateway | `bash scripts/audit-server.sh` | Full snapshot — WG, Tor, Privoxy, UFW, routing |
| Gateway | `sudo tcpdump -i enp0s31f6 -n 'udp port 443'` | Whether handshake packets are physically arriving |
| Gateway | `nc -vz <ip> <port>` | LAN reachability test from the gateway |
| Client (Win) | WireGuard app → tunnel → **Log** tab | Handshake initiation/response messages |
| Client (Win) | `ping -f -l <size> <ip>` | Path MTU probe |
| Client (Win) | `Get-NetRoute` (PowerShell) | What's actually routed where |
