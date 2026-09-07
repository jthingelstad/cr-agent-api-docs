"""A local stand-in for the Clash Royale API, scriptable through a rollover.

The season boundary happens once a month and cannot be replayed, so the only
way to know the recorder handles it is to script it: race closes, endpoint
404s for a while, new race appears at section 0. If the tool cannot narrate
this correctly here, it will not narrate it correctly at 10:00 UTC either.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

SENTINEL = "19691231T235959.000Z"


def race(section: int, period: int, period_type: str, fame: int) -> dict:
    return {
        "state": "full",
        "sectionIndex": section,
        "periodIndex": period,
        "periodType": period_type,
        "clan": {"tag": "#CLAN", "name": "Test Clan", "fame": fame, "periodPoints": 0},
        "clans": [{"tag": "#OTHER", "name": "Rival", "fame": 100}],
        "periodLogs": [],
    }


class Script:
    """Responses served in order; each entry is (status, body, repeat_count)."""

    def __init__(self, steps: list[tuple[str, int, object, int]]):
        self._queue: list[tuple[str, int, object]] = []
        for path_key, status, body, repeat in steps:
            self._queue.extend([(path_key, status, body)] * repeat)
        self._index = 0
        self.calls: list[str] = []
        self._lock = threading.Lock()

    def next_for(self, path: str):
        with self._lock:
            self.calls.append(path)
            for offset in range(self._index, len(self._queue)):
                key, status, body = self._queue[offset]
                if key in path:
                    self._index = offset + 1
                    return status, body
            # Past the end of the script: hold the last matching state.
            for key, status, body in reversed(self._queue):
                if key in path:
                    return status, body
            return 404, {"reason": "notFound"}


class _Handler(BaseHTTPRequestHandler):
    script: Script = None  # type: ignore[assignment]

    def do_GET(self):  # noqa: N802
        if self.headers.get("Authorization") != "Bearer test-token":
            self._send(403, {"reason": "accessDenied", "message": "invalid authorization"})
            return
        status, body = self.script.next_for(self.path)
        self._send(status, body)

    def _send(self, status: int, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


class FakeAPI:
    def __init__(self, script: Script):
        handler = type("H", (_Handler,), {"script": script})
        self.server = HTTPServer(("127.0.0.1", 0), handler)
        self.script = script
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}/v1"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()
