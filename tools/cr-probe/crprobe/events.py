"""Turning a stream of polls into the few moments that mattered.

A watch that printed every poll would bury the interesting instant. This emits
only transitions, and it is deliberately honest about precision: polling every
5s cannot know when a 404 began, only that it began between two observations.
Every transition therefore carries `between` bounds rather than a single
timestamp that looks exact and is not.

That distinction is the whole reason this module exists. On 2026-09-07 the
season-roll 404 window was reported as "10:00 to about 10:09" because nobody
was measuring it; the second figure came from a screenshot.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from deepdiff import DeepDiff

from .store import utcnow


def redact_payload(node):
    """Replace player/clan identity with stable pseudonyms.

    Tags are hashed rather than dropped so a redacted capture still shows that
    the same player appears twice. Lets a capture be cited as evidence in a
    public repo without publishing real people.
    """
    import hashlib

    def pseudo(value: str, prefix: str) -> str:
        digest = hashlib.sha256(value.encode()).hexdigest()[:8].upper()
        return f"{prefix}{digest}"

    def walk(node):
        if isinstance(node, dict):
            out = {}
            for key, val in node.items():
                if key == "tag" and isinstance(val, str):
                    out[key] = pseudo(val, "#REDACT")
                elif key == "name" and isinstance(val, str):
                    # Neutral prefix: a `name` here may belong to a player or a
                    # clan and there is no reliable way to tell, so do not
                    # assert one.
                    out[key] = pseudo(val, "redacted-")
                else:
                    out[key] = walk(val)
            return out
        if isinstance(node, list):
            return [walk(item) for item in node]
        return node

    return walk(node)


@dataclass
class PathState:
    """What we last saw at one endpoint, so the next poll can be compared."""

    path: str
    status: int | None = None
    body: object | None = None
    last_seen_at: str | None = None
    fields: tuple[str, ...] = field(default=())
    # True once a non-200 has interrupted the stream, so the next successful
    # diff can be labelled as spanning that gap.
    gapped: bool = False

    def observe(self, response) -> list[dict]:
        """Compare a fresh response to the last one; return transition events."""
        now = utcnow()
        events: list[dict] = []
        previous_at = self.last_seen_at

        if response.status != self.status:
            events.append(
                {
                    "kind": "status_change",
                    "at": now,
                    "path": self.path,
                    "from": self.status,
                    "to": response.status,
                    "reason": response.reason,
                    # The transition happened somewhere in here. Say so.
                    "between": {"after": previous_at, "by": now},
                    "note": _status_note(self.status, response.status, response),
                }
            )

        if response.ok and self.body is not None and response.body != self.body:
            changes = self._field_events(self.body, response.body, now)
            if self.gapped:
                # This diff spans a window where the endpoint was unavailable,
                # so it compares across the gap rather than poll-to-poll. Say
                # so, but DO produce it: at a season roll this is the single
                # most informative comparison there is (sectionIndex 4 -> 0,
                # periodIndex 34 -> 0, colosseum -> training), and discarding
                # the pre-gap state made the tool go quiet exactly when the
                # thing it exists to observe finally happened.
                for change in changes:
                    change["across_gap"] = True
            events.extend(changes)

        if response.error:
            # Never let a failed poll masquerade as "nothing changed" — a gap
            # in the record has to be visible or the timeline lies.
            events.append({"kind": "poll_error", "at": now, "path": self.path,
                           "error": response.error})

        if response.ok:
            self.body = response.body
            self.gapped = False
        elif response.status != 0:
            # Keep the last good body. It is the only thing the post-gap
            # payload can be compared against, and a 404 is a statement about
            # availability, not evidence the previous state was wrong.
            self.gapped = True
        self.status = response.status
        self.last_seen_at = now
        return events

    def _field_events(self, old, new, now: str) -> list[dict]:
        # verbose_level must be >=1 or values_changed comes back empty and every
        # real change silently degrades into a bare 'payload_change'.
        diff = DeepDiff(old, new, ignore_order=True, verbose_level=2)
        changes: list[dict] = []
        # iterable_item_* matter as much as the dict keys: a river race log
        # gaining an entry, a clan joining a race, a participant appearing.
        # Without them a list change degraded to a contentless payload_change.
        for kind, key in (("values_changed", "changed"), ("type_changes", "changed"),
                          ("dictionary_item_added", "added"),
                          ("dictionary_item_removed", "removed"),
                          ("iterable_item_added", "added"),
                          ("iterable_item_removed", "removed")):
            for entry in diff.get(kind, []) or []:
                pointer = _pretty_pointer(entry if isinstance(entry, str) else str(entry))
                if self.fields and not _matches(pointer, self.fields):
                    continue
                item = {"kind": "field_change", "at": now, "path": self.path,
                        "field": pointer, "change": key}
                container = diff.get(kind)
                if isinstance(container, dict):
                    detail = container[entry]
                    if isinstance(detail, dict) and {"old_value", "new_value"} & detail.keys():
                        item["from"] = _small(detail.get("old_value"))
                        item["to"] = _small(detail.get("new_value"))
                    else:
                        # iterable_item_* carry the value itself, not a pair.
                        item["to" if key == "added" else "from"] = _small(detail)
                changes.append(item)
        if not changes and not self.fields:
            # Something moved but nothing scalar surfaced (list churn, ordering).
            return [{"kind": "payload_change", "at": now, "path": self.path,
                     "note": "payload differs with no scalar field change"}]
        # A busy war day can change hundreds of participant fields; a wall of
        # them is not a signal. Cap and count.
        if len(changes) > 40:
            head = changes[:40]
            head.append({"kind": "field_change_overflow", "at": now, "path": self.path,
                         "suppressed": len(changes) - 40})
            return head
        return changes


def _status_note(old: int | None, new: int, response) -> str | None:
    if new == 404 and old == 200:
        return ("endpoint stopped resolving; for currentriverrace this is the "
                "normal between-races window, not a deleted clan")
    if new == 200 and old == 404:
        return "endpoint came back"
    if response.is_invalid_ip:
        return "403 naming an IP: this key is allowlisted for a different network"
    if new == 429:
        return "rate limited"
    return None


_ROOT_RE = re.compile(r"^root")


def _pretty_pointer(raw: str) -> str:
    """DeepDiff's `root['a'][0]['b']` is noisy; `a[0].b` reads better."""
    out = _ROOT_RE.sub("", raw)
    out = re.sub(r"\['([^']*)'\]", r".\1", out)
    return out.lstrip(".") or "(root)"


def _matches(pointer: str, patterns: tuple[str, ...]) -> bool:
    return any(p.lower() in pointer.lower() for p in patterns)


def _small(value):
    """Keep event lines readable — a diff should not paste a whole roster."""
    if isinstance(value, (dict, list)):
        return f"<{type(value).__name__} len {len(value)}>"
    if isinstance(value, str) and len(value) > 120:
        return value[:117] + "..."
    return value
