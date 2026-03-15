"""UFW rule helpers — builds rule strings, never runs sudo directly."""

import subprocess


def get_ufw_status() -> str:
    try:
        return subprocess.check_output(["sudo", "ufw", "status", "verbose"],
                                       stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        return e.output.decode()
    except FileNotFoundError:
        return "UFW not found."


def build_ufw_rules(wg_port: int = 51820, interface: str = "eth0") -> list[str]:
    """Return the list of UFW commands needed for WireGuard."""
    return [
        f"ufw allow {wg_port}/udp",
        "ufw allow OpenSSH",
        f"ufw route allow in on wg0 out on {interface}",
        "ufw --force enable",
    ]


def print_ufw_rules(wg_port: int = 51820, interface: str = "eth0") -> None:
    """Print the UFW rules that scripts/ufw-rules.sh will apply."""
    rules = build_ufw_rules(wg_port, interface)
    print("UFW rules to be applied:")
    for r in rules:
        print(f"  sudo {r}")
