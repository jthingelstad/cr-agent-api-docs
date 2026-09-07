"""One HTTP path to the Clash Royale API, with the failures named.

Everything the probe does goes through here so that a 404, a 403 from the
wrong IP, and a rate limit are distinguishable in one place instead of at
every call site.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import quote, urlsplit, urlunsplit

import requests

BASE_URL = "https://api.clashroyale.com/v1"
USER_AGENT = "crprobe/0.1 (+cr-agent-api-docs)"


@dataclass
class Response:
    """A single call's outcome, flattened for logging and event emission."""

    status: int
    body: object
    elapsed_ms: int
    url: str
    key_label: str
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == 200

    @property
    def reason(self) -> str | None:
        if isinstance(self.body, dict):
            return self.body.get("reason")
        return None

    @property
    def is_invalid_ip(self) -> bool:
        """The 403 that means "right key, wrong network" — the most common
        confusion when a key is shared with deployed infrastructure."""
        if self.status != 403:
            return False
        blob = f"{self.reason} {(self.body or {}).get('message', '') if isinstance(self.body, dict) else ''}"
        return "ip" in blob.lower()


def normalize_path(path: str) -> str:
    """Accept what a person would type and produce a real URL.

    `#` is the tag sigil, not a URL fragment: `/clans/#ABC` must become
    `/clans/%23ABC` or the tag silently disappears at the first `#`.
    """
    path = path.strip()
    # Strip a pasted full URL by string, NOT with urlsplit: a URL parser treats
    # everything after '#' as a fragment, so urlsplit silently deletes the clan
    # tag. `/v1/clans/#ABC` came back as `/clans/` with the tag gone.
    for prefix in ("https://api.clashroyale.com/v1", "http://api.clashroyale.com/v1"):
        if path.startswith(prefix):
            path = path[len(prefix):]
            break
    else:
        if path.startswith("http"):
            # Some other host (a local fake API in tests): drop scheme+authority
            # up to the first path separator, again without parsing fragments.
            rest = path.split("://", 1)[1]
            path = rest[rest.index("/"):] if "/" in rest else "/"
            if path.startswith("/v1"):
                path = path[3:]
    if not path.startswith("/"):
        path = "/" + path
    head, sep, query = path.partition("?")
    # Encode the tag sigil, leaving an already-encoded %23 alone.
    head = head.replace("%23", "\x00").replace("#", "%23").replace("\x00", "%23")
    return BASE_URL + head + (sep + query if sep else "")


class Client:
    """Requests session bound to one credential, with retry on transient failure."""

    def __init__(self, token: str, key_label: str, *, timeout: float = 15.0):
        self._session = requests.Session()
        self._session.headers.update(
            {"Authorization": f"Bearer {token}", "Accept": "application/json",
             "User-Agent": USER_AGENT}
        )
        self.key_label = key_label
        self.timeout = timeout

    def get(self, path: str, *, retries: int = 2) -> Response:
        url = normalize_path(path)
        last_error = None
        for attempt in range(retries + 1):
            started = time.monotonic()
            try:
                raw = self._session.get(url, timeout=self.timeout)
            except requests.RequestException as exc:
                last_error = str(exc)
                # A blip must not end a long watch; back off and try again.
                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                return Response(0, None, int((time.monotonic() - started) * 1000),
                                url, self.key_label, error=last_error)
            elapsed = int((time.monotonic() - started) * 1000)
            try:
                body = raw.json()
            except ValueError:
                body = raw.text
            if raw.status_code == 429 and attempt < retries:
                time.sleep(float(raw.headers.get("Retry-After", 5)))
                continue
            return Response(raw.status_code, body, elapsed, url, self.key_label)
        return Response(0, None, 0, url, self.key_label, error=last_error)

    def close(self) -> None:
        self._session.close()


def public_ip(timeout: float = 5.0) -> str | None:
    """This machine's outbound IP, for checking a key's allowlist.

    Best effort: if we cannot determine it we say so rather than guess, because
    a wrong answer here sends someone debugging the wrong thing.
    """
    try:
        return requests.get("https://api.ipify.org", timeout=timeout).text.strip()
    except requests.RequestException:
        return None
