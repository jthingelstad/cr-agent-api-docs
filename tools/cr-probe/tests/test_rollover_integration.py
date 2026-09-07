"""End to end: can the recorder actually narrate a season rollover?

This is the scenario the tool exists for and the one that cannot be replayed
in the wild. Everything here runs against a scripted local server, so it is
deterministic and needs no credentials.
"""

from __future__ import annotations

import json

import pytest

from crprobe import client as client_mod
from crprobe import timeline
from crprobe.client import Client
from crprobe.events import PathState
from crprobe.store import Store

from tests.fake_api import FakeAPI, Script, race

RACE = "currentriverrace"


@pytest.fixture
def rollover_server(monkeypatch):
    """Colosseum closes, the endpoint 404s, then a fresh season appears."""
    script = Script([
        (RACE, 200, race(4, 34, "colosseum", 38700), 2),   # final colosseum day
        (RACE, 404, {"reason": "notFound"}, 3),            # between races
        (RACE, 200, race(0, 0, "training", 0), 2),         # new season, week 1
    ])
    with FakeAPI(script) as server:
        monkeypatch.setattr(client_mod, "BASE_URL", server.base_url)
        yield server


def _drain(client, state, store=None, session="s"):
    response = client.get(f"/clans/#CLAN/{RACE}")
    if store:
        store.record_request(session, state.path, response)
    events = state.observe(response)
    if store:
        for event in events:
            store.record_event(session, state.path, event["kind"], event)
    return events


def test_recorder_narrates_the_whole_rollover(rollover_server, tmp_path):
    client = Client("test-token", "test:KEY")
    state = PathState(f"/clans/#CLAN/{RACE}")
    store = Store(tmp_path / "c.db")

    for _ in range(7):
        _drain(client, state, store)

    events = store.events("s")
    statuses = [(e["from"], e["to"]) for e in events if e["kind"] == "status_change"]

    assert statuses == [(None, 200), (200, 404), (404, 200)], (
        "the three transitions that define a rollover must all be captured"
    )


def test_the_404_window_is_bounded_not_guessed(rollover_server, tmp_path):
    client = Client("test-token", "test:KEY")
    state = PathState(f"/clans/#CLAN/{RACE}")
    store = Store(tmp_path / "c.db")
    for _ in range(7):
        _drain(client, state, store)

    (window,) = timeline.windows(store.events("s"))

    assert window["status"] == 404
    assert window["began_after"] and window["began_by"]
    assert window["ended_after"] and window["ended_by"]
    assert window["began_after"] < window["began_by"] <= window["ended_after"] < window["ended_by"]
    bounds = window["duration_bounds"]
    assert bounds["at_least_seconds"] <= bounds["at_most_seconds"]


def test_the_new_season_shape_is_reported_as_field_changes(rollover_server, tmp_path):
    """Section and period returning to 0 is how a consumer learns the season rolled."""
    client = Client("test-token", "test:KEY")
    state = PathState(f"/clans/#CLAN/{RACE}")
    for _ in range(7):
        events = _drain(client, state)
        changed = {e.get("field"): (e.get("from"), e.get("to"))
                   for e in events if e["kind"] == "field_change"}
        if changed:
            last = changed

    assert last["sectionIndex"] == (4, 0)
    assert last["periodIndex"] == (34, 0)
    assert last["periodType"] == ("colosseum", "training")


def test_404_is_explained_as_the_between_races_window(rollover_server):
    client = Client("test-token", "test:KEY")
    state = PathState(f"/clans/#CLAN/{RACE}")
    notes = []
    for _ in range(7):
        for event in _drain(client, state):
            if event["kind"] == "status_change" and event.get("note"):
                notes.append(event["note"])

    assert any("not a deleted clan" in n for n in notes)


def test_timeline_survives_a_session_that_is_still_open(rollover_server, tmp_path):
    """Reading a timeline mid-record must not blow up on an unclosed window."""
    client = Client("test-token", "test:KEY")
    state = PathState(f"/clans/#CLAN/{RACE}")
    store = Store(tmp_path / "c.db")
    for _ in range(4):  # stop while still inside the 404 window
        _drain(client, state, store)

    (window,) = timeline.windows(store.events("s"))

    assert window["status"] == 404
    assert "ended_by" not in window, "an open window must not claim an end"


def test_payload_dedup_across_a_long_run(rollover_server, tmp_path):
    client = Client("test-token", "test:KEY")
    state = PathState(f"/clans/#CLAN/{RACE}")
    store = Store(tmp_path / "c.db")
    for _ in range(7):
        _drain(client, state, store)

    payloads = store._conn.execute("SELECT COUNT(*) FROM payload").fetchone()[0]
    requests = store._conn.execute("SELECT COUNT(*) FROM request").fetchone()[0]

    assert requests == 7
    assert payloads == 3, "colosseum, the 404 body, and the new race — nothing more"


def test_bad_credential_fails_loudly_rather_than_looking_like_a_404(rollover_server):
    client = Client("wrong-token", "test:BAD")
    response = client.get(f"/clans/#CLAN/{RACE}")

    assert response.status == 403
    assert response.reason == "accessDenied"


def test_the_across_gap_diff_is_labelled(rollover_server):
    """The most useful comparison of a rollover spans the 404 window, so it must
    be produced AND marked, not silently presented as a poll-to-poll change."""
    client = Client("test-token", "test:KEY")
    state = PathState(f"/clans/#CLAN/{RACE}")
    marked = []
    for _ in range(7):
        for event in _drain(client, state):
            if event["kind"] == "field_change" and event.get("across_gap"):
                marked.append(event["field"])

    assert "sectionIndex" in marked
    assert "periodIndex" in marked
