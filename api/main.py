"""WG-home-VPN Status API — live peer status, connection history, partial config."""

import ipaddress
import os
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import db

load_dotenv()

app = FastAPI(title="WG-home-VPN API", version="1.0.0")

WG_INTERFACE = os.getenv("WG_INTERFACE", "wg0")
HERE = Path(__file__).parent

static_dir = HERE / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

PEER_NAMES: dict[str, str] = {}
_last_handshake: dict[str, str] = {}


def _run_wg_dump() -> list[str]:
    try:
        out = subprocess.check_output(
            ["sudo", "wg", "show", WG_INTERFACE, "dump"],
            stderr=subprocess.STDOUT,
        ).decode()
        return [l for l in out.splitlines() if l.strip()]
    except Exception:
        return []


def _parse_dump_line(line: str) -> Optional[dict]:
    parts = line.split("\t")
    if len(parts) < 6:
        return None
    return {
        "public_key": parts[0],
        "preshared_key": parts[1],
        "endpoint": parts[2],
        "allowed_ips": parts[3],
        "latest_handshake": parts[4],
        "transfer_rx": int(parts[5]) if parts[5].isdigit() else 0,
        "transfer_tx": int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else 0,
        "persistent_keepalive": parts[7] if len(parts) > 7 else "",
    }


def _parse_peer_name(public_key: str) -> str:
    if public_key in PEER_NAMES:
        return PEER_NAMES[public_key]
    name = public_key[:12] + "..."
    try:
        out = subprocess.check_output(
            ["sudo", "wg", "show", WG_INTERFACE, "peer", public_key],
            stderr=subprocess.DEVNULL,
        ).decode()
        for line in out.splitlines():
            m = re.search(r"allowed ips:\s*(\S+)", line, re.IGNORECASE)
            if m:
                name = m.group(1)
                break
    except Exception:
        pass
    PEER_NAMES[public_key] = name
    return name


def _obfuscate_ip(ip_str: str) -> str:
    if not ip_str or ip_str == "(none)":
        return "(none)"
    addr = ip_str.rsplit(":", 1)[0]
    port = ip_str.rsplit(":", 1)[1] if ":" in ip_str else ""
    try:
        obj = ipaddress.ip_address(addr)
        if isinstance(obj, ipaddress.IPv4Address):
            parts = addr.split(".")
            obfuscated = f"{parts[0]}.{parts[1]}.{parts[2]}.xxx"
        else:
            obfuscated = addr.rsplit(":", 1)[0] + ":xxxx"
    except ValueError:
        obfuscated = addr
    return f"{obfuscated}:{port}" if port else obfuscated


def _format_bytes(b: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if abs(b) < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TiB"


def _format_handshake(ts_str: str) -> dict:
    if not ts_str or ts_str == "0":
        return {"label": "Never", "timestamp": None, "seconds_ago": None}
    try:
        ts = int(ts_str)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        ago = int((now - dt).total_seconds())
        if ago < 60:
            label = f"{ago}s ago"
        elif ago < 3600:
            label = f"{ago // 60}m ago"
        elif ago < 86400:
            label = f"{ago // 3600}h ago"
        else:
            label = f"{ago // 86400}d ago"
        return {"label": label, "timestamp": dt.isoformat(), "seconds_ago": ago}
    except ValueError:
        return {"label": ts_str, "timestamp": None, "seconds_ago": None}


def _track_connections(peers: list[dict]) -> None:
    for p in peers:
        pk = p["public_key"]
        hs = p["latest_handshake"]
        if not hs or hs == "0":
            continue
        prev = _last_handshake.get(pk)
        if prev != hs:
            _last_handshake[pk] = hs
            ep_ip = p["endpoint"].rsplit(":", 1)[0] if p["endpoint"] and p["endpoint"] != "(none)" else "unknown"
            db.upsert_peer(pk, p.get("name", ""))
            db.log_connection(pk, ep_ip, hs)


def _background_tracker(interval: int = 30) -> None:
    while True:
        try:
            lines = _run_wg_dump()
            peers = []
            for line in lines[1:]:
                parsed = _parse_dump_line(line)
                if parsed:
                    parsed["name"] = _parse_peer_name(parsed["public_key"])
                    peers.append(parsed)
            _track_connections(peers)
        except Exception:
            pass
        time.sleep(interval)


@app.on_event("startup")
async def startup() -> None:
    db.init_db()
    thread = threading.Thread(target=_background_tracker, daemon=True)
    thread.start()


@app.get("/api/peers")
def get_peers() -> list[dict]:
    lines = _run_wg_dump()
    result = []
    seen_keys = set()
    for line in lines[1:]:
        parsed = _parse_dump_line(line)
        if not parsed:
            continue
        pk = parsed["public_key"]
        seen_keys.add(pk)
        name = _parse_peer_name(pk)
        hs = _format_handshake(parsed["latest_handshake"])
        epoch = int(parsed["latest_handshake"]) if parsed["latest_handshake"].isdigit() else 0
        now = int(time.time())
        connected = (now - epoch) < 180 if epoch > 0 else False
        result.append({
            "name": name,
            "public_key": pk[:16] + "..." + pk[-4:],
            "endpoint": _obfuscate_ip(parsed["endpoint"]),
            "allowed_ips": parsed["allowed_ips"],
            "connected": connected,
            "handshake": hs,
            "transfer_rx": _format_bytes(parsed["transfer_rx"]),
            "transfer_tx": _format_bytes(parsed["transfer_tx"]),
            "total_connections": db.get_connection_count(pk),
        })
    known = db.get_all_peers()
    for peer in known:
        if peer["public_key"] not in seen_keys:
            result.append({
                "name": peer.get("name", ""),
                "public_key": peer["public_key"][:16] + "..." + peer["public_key"][-4:],
                "endpoint": "(offline)",
                "allowed_ips": "",
                "connected": False,
                "handshake": {"label": "Offline", "timestamp": None, "seconds_ago": None},
                "transfer_rx": "0 B",
                "transfer_tx": "0 B",
                "total_connections": db.get_connection_count(peer["public_key"]),
            })
    return result


@app.get("/api/peers/{public_key:path}/history")
def get_peer_history(public_key: str, limit: int = Query(20, ge=1, le=200)) -> list[dict]:
    pk = public_key.replace("...", "").replace("-", "")
    known = db.get_all_peers()
    matched = [p["public_key"] for p in known if p["public_key"].startswith(pk[:16])]
    if not matched:
        return []
    return db.get_peer_history(matched[0], limit)


@app.get("/api/config")
def get_config() -> dict:
    config: dict = {
        "interface": WG_INTERFACE,
        "server_port": None,
        "server_ip": "10.0.0.1/24",
        "dns": [],
        "peers": [],
    }
    try:
        lines = _run_wg_dump()
        if lines and not lines[0].startswith("interface"):
            pass
        elif lines:
            parts = lines[0].split("\t")
            if len(parts) >= 4:
                config["server_port"] = parts[2] if parts[2] != "0" else None
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ["sudo", "wg", "show", WG_INTERFACE, "private-key"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        pub = subprocess.run(
            ["wg", "pubkey"], input=out, capture_output=True, text=True
        ).stdout.strip()
        config["server_public_key"] = pub[:16] + "..." + pub[-4:]
    except Exception:
        config["server_public_key"] = "unknown"
    try:
        wg0_conf = Path("/etc/wireguard/wg0.conf")
        if wg0_conf.exists():
            text = wg0_conf.read_text()
            m = re.search(r"ListenPort\s*=\s*(\d+)", text)
            if m:
                config["server_port"] = int(m.group(1))
            m = re.search(r"Address\s*=\s*(\S+)", text)
            if m:
                config["server_ip"] = m.group(1)
            m = re.search(r"DNS\s*=\s*(\S+)", text)
            if m:
                config["dns"] = [d.strip() for d in m.group(1).split(",")]
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ["sudo", "wg", "show", WG_INTERFACE, "dump"],
            stderr=subprocess.DEVNULL,
        ).decode()
        for line in out.splitlines()[1:]:
            p = _parse_dump_line(line)
            if p:
                config["peers"].append({
                    "allowed_ips": p["allowed_ips"],
                    "name": _parse_peer_name(p["public_key"]),
                    "public_key": p["public_key"][:12] + "...",
                    "endpoint_config": _obfuscate_ip(p["endpoint"]),
                })
    except Exception:
        pass
    return config


@app.get("/api/summary")
def get_summary() -> dict:
    peers = get_peers()
    connected = [p for p in peers if p["connected"]]
    total_conn = sum(p["total_connections"] for p in peers)
    return {
        "total_peers": len(peers),
        "connected_peers": len(connected),
        "total_connections_recorded": total_conn,
        "interface": WG_INTERFACE,
    }


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (HERE / "templates" / "dashboard.html").read_text()


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8800, reload=False)
