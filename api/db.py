"""SQLite connection tracking for WireGuard peers."""

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "wg_history.db"

_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with _lock, _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS peers (
                public_key TEXT PRIMARY KEY,
                name TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS connection_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                public_key TEXT NOT NULL REFERENCES peers(public_key),
                endpoint_ip TEXT,
                handshake_time TIMESTAMP,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_events_pk ON connection_events(public_key);
            CREATE INDEX IF NOT EXISTS idx_events_detected ON connection_events(detected_at);
        """)


def upsert_peer(public_key: str, name: str = "") -> None:
    with _lock, _get_conn() as conn:
        conn.execute(
            """INSERT INTO peers (public_key, name)
               VALUES (?, ?)
               ON CONFLICT(public_key) DO UPDATE SET name=COALESCE(NULLIF(?,''), name)""",
            (public_key, name, name),
        )


def log_connection(public_key: str, endpoint_ip: str, handshake_time: str) -> None:
    with _lock, _get_conn() as conn:
        conn.execute(
            """INSERT INTO connection_events (public_key, endpoint_ip, handshake_time)
               VALUES (?, ?, ?)""",
            (public_key, endpoint_ip, handshake_time),
        )


def get_connection_count(public_key: str) -> int:
    with _lock, _get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM connection_events WHERE public_key=?",
            (public_key,),
        ).fetchone()
        return row["cnt"] if row else 0


def get_peer_history(public_key: str, limit: int = 50) -> list[dict]:
    with _lock, _get_conn() as conn:
        rows = conn.execute(
            """SELECT endpoint_ip, handshake_time, detected_at
               FROM connection_events
               WHERE public_key=?
               ORDER BY detected_at DESC
               LIMIT ?""",
            (public_key, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_latest_handshake(public_key: str) -> str | None:
    with _lock, _get_conn() as conn:
        row = conn.execute(
            """SELECT handshake_time FROM connection_events
               WHERE public_key=?
               ORDER BY detected_at DESC LIMIT 1""",
            (public_key,),
        ).fetchone()
        return row["handshake_time"] if row else None


def get_all_peers() -> list[dict]:
    with _lock, _get_conn() as conn:
        rows = conn.execute("SELECT * FROM peers ORDER BY name COLLATE NOCASE").fetchall()
        return [dict(r) for r in rows]
