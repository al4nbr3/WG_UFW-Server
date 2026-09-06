# WG-home-VPN — Script Reference

**Status:** Active
**Location:** `~/Wrk-pjtcs/WG-home-VPN`
**What this project is:** A management tool for a WireGuard VPN server + UFW firewall running on a home server (V10L3T4, 192.168.1.195). It gives you a command-line manager for adding/removing VPN clients and checking status, plus a small web dashboard that shows who's connected and tracks connection history over time. An optional Claude-powered assistant can help troubleshoot setup issues.

## Scripts

### `wg_ufw_manager.py`
The interactive command-line entry point for the whole project. Run it as `python wg_ufw_manager.py` with a flag: `--status` (shows WireGuard + UFW status), `--list-clients` (table of registered VPN clients), `--add-client <name>` (generates keys, picks the next free IP, writes a ready-to-import `.conf` file under `config/clients/`), `--remove-client <name>` (deletes the client's saved record), `--ufw-rules` (prints the firewall rules needed for WireGuard), or `--ai` (starts an interactive chat with the Claude assistant for setup help). It never runs `sudo` itself — after adding or removing a client, it tells you which `scripts/*.sh` bash script to run to actually apply the change on the live server. Reads settings like the WireGuard port and DNS servers from a `.env` file.

**Why it's written this way:** One flag per action via `argparse`, rather than subcommands, keeps the CLI flat and predictable for a tool one person runs from memory. The hard rule against calling `sudo` from Python is a deliberate architectural boundary, not an oversight — it means every privileged action on the real server is confined to a small, readable, git-tracked bash script, so there's always a single auditable place to check "what does this actually do to the firewall/interface" instead of that logic being buried in Python subprocess calls. Falling back to `api.ipify.org` for the server's public IP exists only because a home connection's WAN IP isn't guaranteed to be known or static ahead of time; it's a convenience default, not something the tool depends on.

### `lib/wireguard.py`
The engine behind client management — no command-line interaction, just functions. Generates WireGuard key pairs and pre-shared keys by shelling out to the `wg` command-line tool, works out the next free IP address in the VPN subnet (10.0.0.x), and reads/writes each client's record as a JSON file under `config/clients/`. Also builds the actual `.conf` file content a client device would import to connect. A gotcha: `get_wg_status()` calls `wg show` without `sudo`, so on a locked-down box it may report "not found" even when the interface is fine — that's the CLI's `--status` flow, not to be confused with the API's own status probe which does use `sudo`.

**Why it's written this way:** Key generation shells out to the real `wg genkey`/`wg pubkey`/`wg genpsk` binaries instead of reimplementing Curve25519 key generation in Python — WireGuard's own cryptography is what every client and server actually trusts, so there's no reason (and real risk) in hand-rolling that logic. Client records are one flat JSON file per client under `config/clients/` rather than a database: with a handful of home-network peers there's no query need a database would justify, and a plain file per client makes each one trivially readable, diffable, or deleted by hand if something goes wrong. `get_next_client_ip()` just linearly scans for the first free address in a /24 — an O(n) scan is fine because n never exceeds a couple hundred, so a smarter allocation scheme would be solving a problem that doesn't exist here.

### `lib/ufw.py`
Small helper module for the UFW (Uncomplicated Firewall) side of things. `get_ufw_status()` runs `sudo ufw status verbose` and returns the raw text. `build_ufw_rules()` and `print_ufw_rules()` don't touch the firewall — they just compute and print the exact `ufw` commands needed to open the WireGuard port and set up routing, which the human then applies by running `scripts/ufw-rules.sh`. This keeps every actual `sudo` firewall change confined to that one bash script rather than scattered through Python.

**Why it's written this way:** The module is split cleanly along a read/write line — `get_ufw_status()` is allowed to run `sudo` because it's read-only and safe to call automatically, while `build_ufw_rules()`/`print_ufw_rules()` compute the exact same commands a human would type but only ever print them, never execute them. That split is the concrete embodiment of the project's "no sudo mutations from Python" rule: Python is trusted to decide *what* firewall rules are needed, but only the reviewed `scripts/ufw-rules.sh` bash script is trusted to actually change firewall state.

### `lib/ai_assistant.py`
Wraps the Anthropic Claude API to give the manager an optional AI helper for WireGuard/UFW troubleshooting on Ubuntu 24.04. `ask()` sends a one-off question (with optional context) and returns Claude's answer as text; `interactive_chat()` runs a back-and-forth terminal chat session, keeping conversation history for the length of the session. Needs `ANTHROPIC_API_KEY` set in `.env` — if it's missing, both functions print a clear "AI assistant unavailable" message instead of failing. The system prompt specifically instructs Claude to recommend the project's own `scripts/` bash scripts rather than telling the user to run `sudo` commands by hand.

**Why it's written this way:** The AI helper is deliberately optional and fails soft — `get_client()` returns `None` when there's no API key, and both `ask()` and `interactive_chat()` just print a friendly message instead of raising, so core VPN management never depends on an external API being reachable or paid for. The system prompt's explicit instruction to recommend `scripts/` rather than raw `sudo` commands extends the project's "never sudo directly" rule into the AI's own advice — without it, an assistant answering "how do I open this port" would naturally suggest a raw `sudo ufw` command, undermining the whole design. Conversation history is kept only as an in-memory Python list for the life of one terminal session — there's no reason to persist it since each chat is a one-off troubleshooting session, not a resumable conversation.

### `lib/__init__.py`
Empty file that marks `lib/` as a Python package so `wg_ufw_manager.py` can `import` the wireguard/ufw/ai_assistant modules from it. No logic of its own.

**Why it's written this way:** Nothing notable — it's an empty package marker with no design decisions of its own.

## api/

### `api/main.py`
The FastAPI web service (runs on port 8800, deployed as the `wg-api.service` systemd unit on the remote server) that powers the live status dashboard. On startup it launches a background thread that polls `wg show wg0 dump` every 30 seconds, and whenever a peer's handshake timestamp changes it logs that connection event to the SQLite database via `api/db.py`. Exposes read-only JSON endpoints: `/api/peers` (each peer's connection state, transfer totals, and obfuscated endpoint IP so raw addresses aren't exposed), `/api/peers/{key}/history` (that peer's past connections), `/api/config` (server settings read from `/etc/wireguard/wg0.conf`, with keys partially masked), and `/api/summary` (quick totals). The root `/` route serves an HTML dashboard page from `templates/dashboard.html`. All the privileged `wg`/`ufw` shell-outs use `sudo`, so this service needs passwordless sudo configured for those specific commands on the server it runs on.

**Why it's written this way:** Connection state is tracked by polling `wg show wg0 dump` every 30 seconds on a background thread rather than reacting to events, because WireGuard itself has no push notification or webhook mechanism for handshake changes — polling is the only option, and 30 seconds is a deliberate compromise between dashboard freshness and the cost of an extra `sudo` subprocess call. This service is the one place in the whole project that breaks the "never sudo from Python" rule used by the CLI side — but it's an intentional exception: it runs as a long-lived systemd service with no human present to type a password, so the trade-off is a narrowly-scoped passwordless sudo entry for specific read-only `wg`/`ufw` commands, documented and confined to this one process rather than sprinkled through user-invoked tools. Endpoint IPs are obfuscated (last octet/segment masked) before being served because this is a status dashboard that could be viewed on a shared screen or browser history, and there's no operational need for a viewer to see a peer's exact source IP. Peer name lookups and last-handshake state are cached in simple in-process dicts (`PEER_NAMES`, `_last_handshake`) rather than persisted — losing that cache on a service restart is harmless since it only exists to detect "has this changed since the last poll," and the durable history that actually matters is written to SQLite.

### `api/db.py`
The SQLite persistence layer behind the dashboard's connection history. Manages a `wg_history.db` file (created automatically next to this module) with two tables: `peers` (one row per public key, with a friendly name) and `connection_events` (a timestamped log of handshakes and source IPs). Every write goes through a thread lock and uses WAL journal mode, since the API's background tracker and its request handlers can call into it concurrently. Provides simple query functions used by `api/main.py`: `get_connection_count`, `get_peer_history`, `get_latest_handshake`, and `get_all_peers`.

**Why it's written this way:** SQLite is the obvious choice for a single-process, embedded dashboard that just needs durable history — running a separate database server would be overkill for a handful of peers and a modest event log. WAL journal mode plus an explicit `threading.Lock()` around every connection is a deliberate belt-and-suspenders response to a real concurrency hazard specific to this app: the background tracker thread writes new connection events while request handlers are simultaneously reading (or writing, on `upsert_peer`) from the same file, and SQLite's default rollback journal is prone to "database is locked" errors under exactly that kind of concurrent access — WAL mode makes readers and writers less likely to block each other, and the lock adds an extra layer of safety on top. The `connection_events.public_key` foreign key against `peers` keeps the schema honest (no orphaned history rows) without needing any application-level validation.

### `api/__init__.py`
Empty file that marks `api/` as a Python package so `api.main` and `api.db` can be imported. No logic of its own.

**Why it's written this way:** Nothing notable — it's an empty package marker with no design decisions of its own.

## Deploy / manage

Deployment and every privileged operation for this project run through the bash scripts in `scripts/` (e.g. `scripts/deploy.sh`, `scripts/deploy-api.sh`, `scripts/add-client.sh`, `scripts/ufw-rules.sh`) — see the project's `CLAUDE.md` for the full list. Those scripts are outside this Python file list and not covered here.

---

Note: a second working copy of this same repo also exists on disk at ~/Wrk-pjtcs/Linux_Scripts/Scripts-linux/WG-home-VPN — same code, not a separate project.
