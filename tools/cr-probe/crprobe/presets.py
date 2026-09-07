"""Endpoint sets worth watching together.

A season roll is not visible at one endpoint. It shows up as a race that stops
resolving, a war log that gains an entry, and a player profile whose
previousSeason flips -- and those happen at different minutes. Watching one of
them and inferring the rest is how the September rollover got documented with a
guess in the middle.
"""

from __future__ import annotations

PRESETS: dict[str, dict] = {
    "season-roll": {
        "description": (
            "The monthly season boundary: the race closing, the log entry appearing, "
            "the 404 window, the new race, and the profile's previousSeason flip."
        ),
        "paths": [
            "/clans/{clan}/currentriverrace",
            "/clans/{clan}/riverracelog?limit=1",
            "/players/{player}",
        ],
        # Everything else on these endpoints is battle-day churn.
        "fields": [
            "sectionIndex", "periodIndex", "periodType", "state",
            "clan.fame", "clan.periodPoints", "clan.clanScore",
            "items[0].seasonId", "items[0].createdDate", "items[0].sectionIndex",
            "leagueStatistics", "currentPathOfLegendSeasonResult",
            "lastPathOfLegendSeasonResult", "trophies", "arena",
        ],
        "requires": ("clan", "player"),
        "suggested_interval": 15,
    },
    "war-day": {
        "description": "A single war day: fame accrual, deck usage and the daily reset.",
        "paths": ["/clans/{clan}/currentriverrace"],
        "fields": ["periodIndex", "periodType", "clan.fame", "clan.periodPoints",
                   "state", "sectionIndex"],
        "requires": ("clan",),
        "suggested_interval": 60,
    },
    "raw": {
        "description": "Watch the given paths with no field filter at all.",
        "paths": [],
        "fields": [],
        "requires": (),
        "suggested_interval": 5,
    },
}


def resolve(name: str, *, clan: str | None, player: str | None) -> tuple[list[str], list[str], int]:
    preset = PRESETS[name]
    supplied = {"clan": clan, "player": player}
    missing = [need for need in preset["requires"] if not supplied.get(need)]
    if missing:
        raise ValueError(
            f"preset '{name}' needs {' and '.join('--' + m for m in missing)}"
        )
    paths = [p.format(clan=clan or "", player=player or "") for p in preset["paths"]]
    return paths, list(preset["fields"]), preset["suggested_interval"]
