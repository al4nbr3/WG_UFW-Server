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
WG_PORT=51820
WG_SERVER_IP=10.0.0.1
WG_DNS=1.1.1.1, 8.8.8.8
ANTHROPIC_API_KEY=your_key_here   # optional
```

**4. Run the server setup script**

```bash
sudo bash scripts/install.sh
sudo bash scripts/configure-server.sh
```

**5. Apply UFW firewall rules**

```bash
sudo bash scripts/ufw-rules.sh
```

**6. Start WireGuard**

```bash
sudo bash scripts/start-wg.sh
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
sudo bash scripts/remove-client.sh clientname
```

### Stop WireGuard

```bash
sudo bash scripts/stop-wg.sh
```

### Backup Configuration

```bash
sudo bash scripts/backup.sh
```

### Cleanup Server

```bash
sudo bash scripts/cleanup-server.sh
```

## AI Assistant

If `ANTHROPIC_API_KEY` is set in `.env`, you can ask the AI assistant for help:

```bash
python wg_ufw_manager.py --ask "How do I add a client for a mobile device?"
```

## Scripts Reference

| Script | Description |
|--------|-------------|
| `install.sh` | Installs WireGuard and dependencies |
| `configure-server.sh` | Generates server keys and config |
| `ufw-rules.sh` | Sets UFW rules for VPN traffic |
| `start-wg.sh` | Starts the WireGuard interface |
| `stop-wg.sh` | Stops the WireGuard interface |
| `add-client.sh` | Adds a new VPN client |
| `remove-client.sh` | Removes a VPN client |
| `status.sh` | Shows WireGuard and UFW status |
| `backup.sh` | Backs up server configuration |
| `cleanup-server.sh` | Removes WireGuard and resets UFW |
| `deploy.sh` | Full automated deployment |
