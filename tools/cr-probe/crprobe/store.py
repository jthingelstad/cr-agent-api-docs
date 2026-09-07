"""The capture archive: every request and payload, kept for later review.

Two things this is for. Comparing a rollover to the previous one -- in
September we wanted August's raw payloads and had only the river race log,
because nothing had kept them. And backing a documented claim with the
evidence it came from.

Payloads are content-addressed and deduplicated: polling every 5s produces
mostly identical bodies, and storing each one would make the archive enormous
while hiding the moments that actually differ.

This database lives in a PUBLIC repo's working tree. It is gitignored, and
`--redact` exists so a capture can be cited without publishing real players.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS payload (
    sha256      TEXT PRIMARY KEY,
    body_json   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS request (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session     TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    path        TEXT NOT NULL,
    url         TEXT NOT NULL,
    status      INTEGER NOT NULL,
    elapsed_ms  INTEGER NOT NULL,
    key_label   TEXT,
    error       TEXT,
    sha256      TEXT REFERENCES payload(sha256)
);
CREATE INDEX IF NOT EXISTS request_by_session ON request (session, path, observed_at);
CREATE TABLE IF NOT EXISTS event (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session     TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    path        TEXT NOT NULL,
    kind        TEXT NOT NULL,
    detail_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS event_by_session ON event (session, observed_at);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def default_db_path() -> Path:
    return Path(__file__).resolve().parents[3] / "captures" / "crprobe.db"


class Store:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, timeout=30.0)
        self._conn.row_factory = sqlite3.Row
        # WAL so a `crprobe timeline` can read a session while a four-hour
        # `record` is still writing it, and a generous busy timeout so a
        # concurrent writer waits instead of killing an unattended run.
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def record_request(self, session: str, path: str, response, *, redact=None) -> None:
        body = response.body
        if redact is not None and body is not None:
            body = redact(body)
        sha = None
        if body is not None:
            blob = json.dumps(body, sort_keys=True, separators=(",", ":"))
            sha = hashlib.sha256(blob.encode()).hexdigest()
            self._conn.execute(
                "INSERT OR IGNORE INTO payload (sha256, body_json) VALUES (?, ?)", (sha, blob)
            )
        self._conn.execute(
            "INSERT INTO request (session, observed_at, path, url, status, elapsed_ms,"
            " key_label, error, sha256) VALUES (?,?,?,?,?,?,?,?,?)",
            (session, utcnow(), path, response.url, response.status,
             response.elapsed_ms, response.key_label, response.error, sha),
        )
        self._conn.commit()

    def record_event(self, session: str, path: str, kind: str, detail: dict) -> None:
        self._conn.execute(
            "INSERT INTO event (session, observed_at, path, kind, detail_json) VALUES (?,?,?,?,?)",
            (session, detail.get("at") or utcnow(), path, kind, json.dumps(detail)),
        )
        self._conn.commit()

    def events(self, session: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT observed_at, path, kind, detail_json FROM event WHERE session = ?"
            " ORDER BY observed_at, id", (session,)
        ).fetchall()
        return [
            {"at": r["observed_at"], "path": r["path"], "kind": r["kind"],
             **json.loads(r["detail_json"])}
            for r in rows
        ]

    def sessions(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT session, COUNT(*) AS requests, MIN(observed_at) AS started,"
            " MAX(observed_at) AS ended FROM request GROUP BY session ORDER BY started DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def payload(self, sha: str) -> object | None:
        row = self._conn.execute("SELECT body_json FROM payload WHERE sha256 = ?", (sha,)).fetchone()
        return json.loads(row["body_json"]) if row else None

    def requests_for(self, session: str, path: str | None = None) -> list[dict]:
        sql = ("SELECT observed_at, path, status, elapsed_ms, sha256, error FROM request"
               " WHERE session = ?")
        args: list = [session]
        if path:
            sql += " AND path = ?"
            args.append(path)
        sql += " ORDER BY observed_at, id"
        return [dict(r) for r in self._conn.execute(sql, args).fetchall()]

    def close(self) -> None:
        with closing(self._conn):
            pass
