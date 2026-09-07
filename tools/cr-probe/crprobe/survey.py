"""Checking a claim against every week the API still remembers.

Written because a documented rule was nearly published off a single
observation. The Colosseum finishTime rule looked obvious after one week; it
only became trustworthy after ten, and the ten-week check was a throwaway
script nobody could rerun.

A survey returns rows plus a verdict, so the evidence table in the docs and the
claim above it come from the same command.
"""

from __future__ import annotations

SENTINEL_FINISH_TIME = "19691231T235959.000Z"


def finish_time(client, clan: str, limit: int = 10) -> dict:
    """Does a real `finishTime` appear only in NON-Colosseum weeks?

    Colosseum has no finish line, so no clan in that week hits a completion
    condition and every standings entry carries the epoch-zero sentinel --
    including rank 1, which the general rule would not lead you to expect.
    """
    response = client.get(f"/clans/{clan}/riverracelog?limit={limit}")
    if not response.ok:
        return {"error": f"riverracelog returned {response.status}", "rows": []}

    rows = []
    for item in (response.body or {}).get("items", []):
        standings = item.get("standings") or []
        rank_one = next((s for s in standings if s.get("rank") == 1), standings[0] if standings else None)
        if rank_one is None:
            continue
        finish = (rank_one.get("clan") or {}).get("finishTime")
        # Colosseum stakes are +-100 trophies against +-20 for a normal week,
        # which identifies the week without needing the live periodType.
        colosseum = abs(rank_one.get("trophyChange") or 0) == 100
        all_sentinel = all(
            ((s.get("clan") or {}).get("finishTime") == SENTINEL_FINISH_TIME) for s in standings
        )
        rows.append(
            {
                "season": item.get("seasonId"),
                "section": item.get("sectionIndex"),
                "created": item.get("createdDate"),
                "colosseum": colosseum,
                "rank1_finish_time": finish,
                "rank1_is_sentinel": finish == SENTINEL_FINISH_TIME,
                "all_sentinel": all_sentinel,
            }
        )

    colosseum_rows = [r for r in rows if r["colosseum"]]
    normal_rows = [r for r in rows if not r["colosseum"]]
    holds = (
        bool(colosseum_rows)
        and all(r["all_sentinel"] for r in colosseum_rows)
        and all(not r["rank1_is_sentinel"] for r in normal_rows)
    )
    return {
        "claim": "Colosseum weeks are all-sentinel finishTime; normal weeks give rank 1 a real one",
        "holds": holds,
        "weeks": len(rows),
        "colosseum_weeks": len(colosseum_rows),
        "normal_weeks": len(normal_rows),
        "rows": rows,
    }


def week_close(client, clan: str, limit: int = 10) -> dict:
    """When does a war week actually close, and does it drift?

    The season hour is fixed at 10:00Z but the weekly race close is not, and
    conflating the two is what produced a phantom season. Grouped by season so
    the within-season stability and between-season drift are both visible.
    """
    response = client.get(f"/clans/{clan}/riverracelog?limit={limit}")
    if not response.ok:
        return {"error": f"riverracelog returned {response.status}", "rows": []}

    by_season: dict[int, list[str]] = {}
    rows = []
    for item in (response.body or {}).get("items", []):
        created = item.get("createdDate") or ""
        season = item.get("seasonId")
        rows.append({"season": season, "section": item.get("sectionIndex"), "created": created})
        # createdDate is compact ISO: 20260907T093404.000Z
        clock = created[9:15] if len(created) >= 15 else ""
        by_season.setdefault(season, []).append(clock)

    return {
        "claim": "weekly race close is stable within a season and drifts between seasons",
        "rows": rows,
        "close_times_by_season": {
            season: sorted(set(times)) for season, times in sorted(by_season.items())
        },
    }


SURVEYS = {"finish-time": finish_time, "week-close": week_close}
