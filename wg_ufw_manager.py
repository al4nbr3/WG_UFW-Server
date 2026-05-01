#!/usr/bin/env python3
"""WG-home-VPN — WireGuard + UFW manager with optional Claude AI assistant."""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

load_dotenv()

from lib import wireguard, ufw, ai_assistant

console = Console()


def cmd_status() -> None:
    console.print(Panel("[bold]WireGuard Status[/bold]", style="green"))
    console.print(wireguard.get_wg_status())

    console.print(Panel("[bold]UFW Status[/bold]", style="blue"))
    console.print(ufw.get_ufw_status())


def cmd_list_clients() -> None:
    clients = wireguard.list_clients()
    if not clients:
        console.print("[yellow]No clients registered yet.[/yellow]")
        return

    table = Table(title="Registered WireGuard Clients")
    table.add_column("Name", style="cyan")
    table.add_column("IP", style="green")
    table.add_column("Public Key", style="dim")

    for c in clients:
        table.add_row(c["name"], c["ip"], c["public_key"][:24] + "...")

    console.print(table)


def cmd_add_client(name: str) -> None:
    if not name:
        console.print("[red]Usage: --add-client <name>[/red]")
        sys.exit(1)

    server_pub = wireguard.load_server_public_key()
    if not server_pub:
        console.print("[red]Server not configured yet. Run scripts/configure-server.sh first.[/red]")
        sys.exit(1)

    server_ip = os.getenv("SERVER_PUBLIC_IP", "")
    if not server_ip:
        import urllib.request
        try:
            server_ip = urllib.request.urlopen("https://api.ipify.org").read().decode()
        except Exception:
            server_ip = "YOUR.SERVER.IP"

    wg_port = int(os.getenv("WG_PORT", "51820"))
    dns = os.getenv("WG_DNS", "1.1.1.1, 8.8.8.8")
    subnet_base = os.getenv("WG_SERVER_IP", "10.0.0.1").rsplit(".", 1)[0]

    private_key, public_key = wireguard.generate_keypair()
    psk = wireguard.generate_preshared_key()
    client_ip = wireguard.get_next_client_ip(subnet_base)

    wireguard.save_client(name, public_key, client_ip, psk)

    config = wireguard.build_client_config(
        name=name,
        client_private_key=private_key,
        client_ip=client_ip,
        server_public_key=server_pub,
        server_endpoint=server_ip,
        wg_port=wg_port,
        dns=dns,
        preshared_key=psk,
    )

    out_path = Path(f"config/clients/{name}.conf")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(config)

    console.print(f"[green]Client '{name}' added:[/green] IP={client_ip}")
    console.print(f"Config saved to: [bold]{out_path}[/bold]")
    console.print("\nTo activate on server, run:")
    console.print(f"  [bold]bash scripts/add-client.sh {name}[/bold]")


def cmd_remove_client(name: str) -> None:
    if wireguard.remove_client(name):
        console.print(f"[green]Client '{name}' removed.[/green]")
        console.print(f"To remove from live server: [bold]bash scripts/remove-client.sh {name}[/bold]")
    else:
        console.print(f"[red]Client '{name}' not found.[/red]")


def cmd_ai() -> None:
    ai_assistant.interactive_chat()


def cmd_ufw_rules() -> None:
    interface = os.getenv("WG_INTERFACE", "eth0")
    wg_port = int(os.getenv("WG_PORT", "51820"))
    ufw.print_ufw_rules(wg_port, interface)
    console.print("\nTo apply: [bold]bash scripts/ufw-rules.sh[/bold]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WG-home-VPN — WireGuard + UFW manager"
    )
    parser.add_argument("--status", action="store_true", help="Show WireGuard + UFW status")
    parser.add_argument("--list-clients", action="store_true", help="List registered clients")
    parser.add_argument("--add-client", metavar="NAME", help="Add a new WireGuard client")
    parser.add_argument("--remove-client", metavar="NAME", help="Remove a WireGuard client")
    parser.add_argument("--ufw-rules", action="store_true", help="Show UFW rules to apply")
    parser.add_argument("--ai", action="store_true", help="Start interactive AI assistant")

    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.list_clients:
        cmd_list_clients()
    elif args.add_client:
        cmd_add_client(args.add_client)
    elif args.remove_client:
        cmd_remove_client(args.remove_client)
    elif args.ufw_rules:
        cmd_ufw_rules()
    elif args.ai:
        cmd_ai()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
