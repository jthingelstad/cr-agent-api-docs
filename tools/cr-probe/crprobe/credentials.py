"""Finding a usable Clash Royale API key without being told its name.

The point is that you can hand this the .env of whatever you are debugging --
`--key-file ~/Projects/clash-royale/elixir-mcp/.env` -- and probe with the SAME credential
that service uses, IP binding and all. "Works for me but not for the service"
is otherwise very hard to answer.

Detection is positive, not a name guess. Supercell API keys are JWTs, so any
value that decodes as one is a candidate and its claims say whether Supercell
issued it. Name heuristics are only a fallback, and a live call is the final
arbiter -- so if the claim shape ever changes, this degrades to "try each
candidate" rather than breaking.

Key VALUES are never logged, printed, or stored. Candidates are identified to
the user as `file:VARNAME`.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network
from pathlib import Path

import jwt
from dotenv import dotenv_values

# Values whose NAME suggests a key, used only when the value is not JWT-shaped.
_NAME_HINT = re.compile(r"(CR|CLASH|ROYALE|SUPERCELL).*(KEY|TOKEN)|^(API_)?(KEY|TOKEN)$", re.I)

# A .env is a junk drawer: AWS, GitHub and Discord secrets all match "KEY" or
# "TOKEN" too. Probing them wastes an API call each and produces a wall of 403s
# that buries the real answer, so rule them out by name before trying them.
_NOT_OURS = re.compile(
    r"AWS|GITHUB|GITLAB|OPENAI|ANTHROPIC|CLAUDE|DISCORD|SLACK|STRIPE|TWILIO|"
    r"SENTRY|DATADOG|BUTTONDOWN|FASTMAIL|TINYLYTICS|SECRET_ACCESS|SESSION|"
    r"WEBHOOK|DATABASE|POSTGRES|REDIS",
    re.I,
)

# Files searched when none are given. Ordered by how likely they are to hold a
# key that works from THIS machine rather than from deployed infrastructure.
DEFAULT_KEY_FILES = (
    "~/Projects/clash-royale/drop.poapkings.com/.env",
    "~/Projects/clash-royale/elixir-bot/.env",
    "~/Projects/clash-royale/elixir-mcp/.env",
    "~/Projects/clash-royale/cr-agent-api-docs/.env",
    "./.env",
)


@dataclass
class Candidate:
    """One possible API key. `value` is never rendered — see `label`."""

    source: str
    name: str
    value: str = field(repr=False)
    claims: dict | None = None

    @property
    def label(self) -> str:
        return f"{self.source}:{self.name}"

    @property
    def is_jwt(self) -> bool:
        return self.claims is not None

    @property
    def issuer(self) -> str | None:
        return (self.claims or {}).get("iss")

    @property
    def looks_supercell(self) -> bool:
        blob = json.dumps(self.claims or {}).lower()
        return "supercell" in blob

    @property
    def allowed_cidrs(self) -> list[str]:
        """IP allowlist carried in the token, if it carries one.

        Supercell binds keys to IPs, and a key used from the wrong network
        fails with 403 invalidIp. Surfacing the allowlist turns that from a
        mystery into an answer. The claim layout is not contractual, so this
        walks the payload for anything CIDR-shaped instead of assuming a path.
        """
        found: list[str] = []

        def walk(node) -> None:
            if isinstance(node, dict):
                for key, val in node.items():
                    if key.lower() in {"cidrs", "cidr", "ips", "ip"}:
                        for item in val if isinstance(val, list) else [val]:
                            if isinstance(item, str):
                                found.append(item)
                    else:
                        walk(val)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(self.claims or {})
        return found

    def permits_ip(self, ip: str | None) -> bool | None:
        """True/False if the token pins IPs and we know ours; None if unknown."""
        cidrs = self.allowed_cidrs
        if not cidrs or not ip:
            return None
        try:
            addr = ip_address(ip)
        except ValueError:
            return None
        for cidr in cidrs:
            try:
                if addr in ip_network(cidr, strict=False):
                    return True
            except ValueError:
                continue
        return False


def _looks_supercell_claims(claims: dict) -> bool:
    return "supercell" in json.dumps(claims).lower()


def _decode_unverified(value: str) -> dict | None:
    """Read a JWT's claims without verifying it. We are identifying, not trusting."""
    if value.count(".") != 2 or len(value) < 40:
        return None
    try:
        return jwt.decode(value, options={"verify_signature": False})
    except Exception:
        return None


def _read_pairs(path: Path) -> list[tuple[str, str]]:
    """Pull name/value pairs out of a file without caring what shape it is."""
    try:
        text = path.read_text()
    except OSError:
        return []

    # A file holding nothing but the token is a perfectly reasonable thing to
    # be handed, and has no variable name to report.
    stripped = text.strip()
    if stripped and "=" not in stripped and "\n" not in stripped:
        return [("(file contents)", stripped)]

    if path.suffix == ".json":
        try:
            data = json.loads(text)
        except ValueError:
            return []
        return [(k, v) for k, v in data.items() if isinstance(v, str)]

    return [(k, v) for k, v in dotenv_values(path).items() if v]


def discover(key_files: tuple[str, ...] = (), *, name: str | None = None) -> list[Candidate]:
    """Candidates in the order they should be tried.

    JWT-shaped values that look Supercell-issued sort first, then other JWTs,
    then name matches — best guess first, so the usual case costs one call.
    """
    paths = key_files or tuple(
        p for p in DEFAULT_KEY_FILES if Path(p).expanduser().is_file()
    )
    candidates: list[Candidate] = []
    seen: set[str] = set()

    if env_value := os.environ.get("CR_API_KEY_VALUE"):
        candidates.append(Candidate("environment", "CR_API_KEY_VALUE", env_value,
                                    _decode_unverified(env_value)))

    for raw in paths:
        path = Path(raw).expanduser()
        source = _display_source(path)
        for var, value in _read_pairs(path):
            if name and var != name:
                continue
            if value in seen:
                continue
            claims = _decode_unverified(value)
            if claims is not None and not _looks_supercell_claims(claims):
                # A JWT from some other service; not worth an API call.
                continue
            if claims is None and (not _NAME_HINT.search(var) or _NOT_OURS.search(var)):
                continue
            seen.add(value)
            candidates.append(Candidate(source, var, value, claims))

    candidates.sort(key=lambda c: (not c.looks_supercell, not c.is_jwt))
    return candidates


def _display_source(path: Path) -> str:
    """Short, stable label — parent directory plus filename."""
    try:
        rel = path.expanduser().resolve()
    except OSError:
        return str(path)
    return f"{rel.parent.name}/{rel.name}"
