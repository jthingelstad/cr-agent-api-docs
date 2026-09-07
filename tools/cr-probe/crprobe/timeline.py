"""Reconstructing what happened, from a recorded session.

The output is meant to be pasted into the reference docs after a rollover.
Building the September table by hand meant stitching together a war log
timestamp, two screenshots, a bot database and an MCP tool -- and the one
figure that came from a screenshot is the one stated least precisely.

Precision is preserved rather than flattened: a transition observed between
two polls is reported as a window, and gaps where polling failed are shown as
gaps instead of being quietly closed.
"""

from __future__ import annotations

from datetime import datetime

INTERESTING = {"status_change", "poll_error", "field_change_overflow"}


def _parse(ts: str) -> datetime | None:
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
    except (ValueError, TypeError):
        return None


def build(events: list[dict], *, include_fields: bool = True) -> list[dict]:
    """Collapse an event stream into the moments worth writing down."""
    rows: list[dict] = []
    for event in events:
        kind = event.get("kind")
        if kind in INTERESTING or (include_fields and kind in {"field_change", "payload_change"}):
            rows.append(event)
    return rows


def windows(events: list[dict]) -> list[dict]:
    """Spans where an endpoint was in a non-200 state, with honest bounds.

    A window's start is only known to lie between the last good poll and the
    first bad one; the same at the end. Reporting the midpoint would invent
    precision, so both bounds are kept.
    """
    open_state: dict[str, dict] = {}
    out: list[dict] = []
    for event in events:
        if event.get("kind") != "status_change":
            continue
        path, to = event["path"], event.get("to")
        bounds = event.get("between") or {}
        if to != 200:
            open_state[path] = {
                "path": path,
                "status": to,
                "reason": event.get("reason"),
                "began_after": bounds.get("after"),
                "began_by": bounds.get("by"),
            }
        elif path in open_state:
            span = open_state.pop(path)
            span["ended_after"] = bounds.get("after")
            span["ended_by"] = bounds.get("by")
            span["duration_bounds"] = _duration_bounds(span)
            out.append(span)
    out.extend(open_state.values())
    return out


def _duration_bounds(span: dict) -> dict | None:
    """Shortest and longest the window could possibly have been."""
    began_after, began_by = _parse(span.get("began_after")), _parse(span.get("began_by"))
    ended_after, ended_by = _parse(span.get("ended_after")), _parse(span.get("ended_by"))
    if not (began_by and ended_after):
        return None
    shortest = (ended_after - began_by).total_seconds()
    longest = ((ended_by - began_after).total_seconds()
               if began_after and ended_by else None)
    return {
        "at_least_seconds": max(0, round(shortest)),
        "at_most_seconds": round(longest) if longest is not None else None,
    }
