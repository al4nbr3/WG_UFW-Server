"""WireGuard key generation, peer management, and config I/O."""

import subprocess
import os
import json
from pathlib import Path


CLIENTS_DIR = Path("config/clients")
SERVER_CONFIG = Path("config/wg0.conf")


def generate_keypair() -> tuple[str, str]:
    """Generate a WireGuard private/public key pair. Returns (private, public)."""
    private = subprocess.check_output(["wg", "genkey"]).decode().strip()
    public = subprocess.run(
        ["wg", "pubkey"], input=private, capture_output=True, text=True
    ).stdout.strip()
    return private, public


def generate_preshared_key() -> str:
    return subprocess.check_output(["wg", "genpsk"]).decode().strip()


def load_server_public_key() -> str | None:
    key_path = Path("config/server_public.key")
    if key_path.exists():
        return key_path.read_text().strip()
    return None


def list_clients() -> list[dict]:
    """Return all registered clients from config/clients/."""
    CLIENTS_DIR.mkdir(parents=True, exist_ok=True)
    clients = []
    for f in sorted(CLIENTS_DIR.glob("*.json")):
        clients.append(json.loads(f.read_text()))
    return clients


def get_next_client_ip(subnet_base: str = "10.0.0") -> str:
    """Return the next available client IP in the subnet."""
    clients = list_clients()
    used = {c["ip"].split("/")[0] for c in clients}
    for i in range(2, 255):
        ip = f"{subnet_base}.{i}"
        if ip not in used:
            return f"{ip}/32"
    raise RuntimeError("No available IPs in subnet")


def save_client(name: str, public_key: str, ip: str, preshared_key: str = "") -> dict:
    """Persist a client record to config/clients/<name>.json."""
    CLIENTS_DIR.mkdir(parents=True, exist_ok=True)
    record = {"name": name, "public_key": public_key, "ip": ip, "preshared_key": preshared_key}
    path = CLIENTS_DIR / f"{name}.json"
    path.write_text(json.dumps(record, indent=2))
    return record


def remove_client(name: str) -> bool:
    path = CLIENTS_DIR / f"{name}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def build_client_config(
    name: str,
    client_private_key: str,
    client_ip: str,
    server_public_key: str,
    server_endpoint: str,
    wg_port: int = 51820,
    dns: str = "1.1.1.1, 8.8.8.8",
    preshared_key: str = "",
) -> str:
    """Generate a complete wg0.conf for a client device."""
    psk_line = f"PresharedKey = {preshared_key}\n" if preshared_key else ""
    return f"""[Interface]
PrivateKey = {client_private_key}
Address = {client_ip}
DNS = {dns}

[Peer]
PublicKey = {server_public_key}
{psk_line}Endpoint = {server_endpoint}:{wg_port}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""


def get_wg_status() -> str:
    """Return wg show output or an error message."""
    try:
        return subprocess.check_output(["wg", "show"], stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        return e.output.decode()
    except FileNotFoundError:
        return "WireGuard (wg) not found. Run scripts/install.sh first."
