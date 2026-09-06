# WG-home-VPN — Script Reference

**Status:** Active
**Location:** `~/Wrk-pjtcs/WG-home-VPN`
**What this project is:** A management tool for a WireGuard VPN server + UFW firewall running on a home server (V10L3T4, 192.168.1.195). It gives you a command-line manager for adding/removing VPN clients and checking status, plus a small web dashboard that shows who's connected and tracks connection history over time. An optional Claude-powered assistant can help troubleshoot setup issues.

## Scripts

### `wg_ufw_manager.py`
The interactive command-line entry point for the whole project. Run it as `python wg_ufw_manager.py` with a flag: `--status` (shows WireGuard + UFW status), `--list-clients` (table of registered VPN clients), `--add-client <name>` (generates keys, picks the next free IP, writes a ready-to-import `.conf` file under `config/clients/`), `--remove-client <name>` (deletes the client's saved record), `--ufw-rules` (prints the firewall rules needed for WireGuard), or `--ai` (starts an interactive chat with the Claude assistant for setup help). It never runs `sudo` itself — after adding or removing a client, it tells you which `scripts/*.sh` bash script to run to actually apply the change on the live server. Reads settings like the WireGuard port and DNS servers from a `.env` file.

### `lib/wireguard.py`
The engine behind client management — no command-line interaction, just functions. Generates WireGuard key pairs and pre-shared keys by shelling out to the `wg` command-line tool, works out the next free IP address in the VPN subnet (10.0.0.x), and reads/writes each client's record as a JSON file under `config/clients/`. Also builds the actual `.conf` file content a client device would import to connect. A gotcha: `get_wg_status()` calls `wg show` without `sudo`, so on a locked-down box it may report "not found" even when the interface is fine — that's the CLI's `--status` flow, not to be confused with the API's own status probe which does use `sudo`.

### `lib/ufw.py`
Small helper module for the UFW (Uncomplicated Firewall) side of things. `get_ufw_status()` runs `sudo ufw status verbose` and returns the raw text. `build_ufw_rules()` and `print_ufw_rules()` don't touch the firewall — they just compute and print the exact `ufw` commands needed to open the WireGuard port and set up routing, which the human then applies by running `scripts/ufw-rules.sh`. This keeps every actual `sudo` firewall change confined to that one bash script rather than scattered through Python.

### `lib/ai_assistant.py`
Wraps the Anthropic Claude API to give the manager an optional AI helper for WireGuard/UFW troubleshooting on Ubuntu 24.04. `ask()` sends a one-off question (with optional context) and returns Claude's answer as text; `interactive_chat()` runs a back-and-forth terminal chat session, keeping conversation history for the length of the session. Needs `ANTHROPIC_API_KEY` set in `.env` — if it's missing, both functions print a clear "AI assistant unavailable" message instead of failing. The system prompt specifically instructs Claude to recommend the project's own `scripts/` bash scripts rather than telling the user to run `sudo` commands by hand.

### `lib/__init__.py`
Empty file that marks `lib/` as a Python package so `wg_ufw_manager.py` can `import` the wireguard/ufw/ai_assistant modules from it. No logic of its own.

## api/

### `api/main.py`
The FastAPI web service (runs on port 8800, deployed as the `wg-api.service` systemd unit on the remote server) that powers the live status dashboard. On startup it launches a background thread that polls `wg show wg0 dump` every 30 seconds, and whenever a peer's handshake timestamp changes it logs that connection event to the SQLite database via `api/db.py`. Exposes read-only JSON endpoints: `/api/peers` (each peer's connection state, transfer totals, and obfuscated endpoint IP so raw addresses aren't exposed), `/api/peers/{key}/history` (that peer's past connections), `/api/config` (server settings read from `/etc/wireguard/wg0.conf`, with keys partially masked), and `/api/summary` (quick totals). The root `/` route serves an HTML dashboard page from `templates/dashboard.html`. All the privileged `wg`/`ufw` shell-outs use `sudo`, so this service needs passwordless sudo configured for those specific commands on the server it runs on.

### `api/db.py`
The SQLite persistence layer behind the dashboard's connection history. Manages a `wg_history.db` file (created automatically next to this module) with two tables: `peers` (one row per public key, with a friendly name) and `connection_events` (a timestamped log of handshakes and source IPs). Every write goes through a thread lock and uses WAL journal mode, since the API's background tracker and its request handlers can call into it concurrently. Provides simple query functions used by `api/main.py`: `get_connection_count`, `get_peer_history`, `get_latest_handshake`, and `get_all_peers`.

### `api/__init__.py`
Empty file that marks `api/` as a Python package so `api.main` and `api.db` can be imported. No logic of its own.

## Deploy / manage

Deployment and every privileged operation for this project run through the bash scripts in `scripts/` (e.g. `scripts/deploy.sh`, `scripts/deploy-api.sh`, `scripts/add-client.sh`, `scripts/ufw-rules.sh`) — see the project's `CLAUDE.md` for the full list. Those scripts are outside this Python file list and not covered here.

---

Note: a second working copy of this same repo also exists on disk at ~/Wrk-pjtcs/Linux_Scripts/Scripts-linux/WG-home-VPN — same code, not a separate project.
