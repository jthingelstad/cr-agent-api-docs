"""A four-hour unattended run meets things a five-second run never does.

Every failure here must leave the recorder still running and the record
honest — a watch that dies at 03:00 or, worse, silently stops noticing, is
useless for a boundary that happens once a month.
"""

from __future__ import annotations

import json

import pytest
import requests

from crprobe import client as client_mod
from crprobe.client import Client, Response, normalize_path
from crprobe.events import PathState
from crprobe.store import Store

from tests.fake_api import FakeAPI, Script, race

RACE = "currentriverrace"


def resp(status=200, body=None, error=None):
    return Response(status, body, 1, "u", "k", error)


def test_transient_network_failure_is_retried_then_reported(monkeypatch):
    """A blip must not end a watch; a persistent outage must be visible."""
    calls = {"n": 0}

    def boom(*args, **kwargs):
        calls["n"] += 1
        raise requests.ConnectionError("connection reset")

    monkeypatch.setattr(requests.Session, "get", boom)
    monkeypatch.setattr("time.sleep", lambda _s: None)
    client = Client("t", "k")

    response = client.get("/x", retries=2)

    assert calls["n"] == 3, "it should retry before giving up"
    assert response.status == 0 and response.error


def test_a_recovering_blip_does_not_surface_as_an_outage(monkeypatch):
    """One failed attempt followed by success is not an event worth reporting."""
    seq = [requests.ConnectionError("reset"), None]

    class FakeRaw:
        status_code = 200
        text = "{}"

        def json(self):
            return {"ok": True}

    def flaky(*args, **kwargs):
        item = seq.pop(0)
        if isinstance(item, Exception):
            raise item
        return FakeRaw()

    monkeypatch.setattr(requests.Session, "get", flaky)
    monkeypatch.setattr("time.sleep", lambda _s: None)

    response = Client("t", "k").get("/x", retries=2)

    assert response.ok and response.error is None


def test_rate_limit_is_waited_out_using_the_servers_own_hint(monkeypatch):
    slept: list[float] = []

    class Limited:
        status_code = 429
        headers = {"Retry-After": "7"}
        text = "{}"

        def json(self):
            return {"reason": "tooManyRequests"}

    monkeypatch.setattr(requests.Session, "get", lambda *a, **k: Limited())
    monkeypatch.setattr("time.sleep", lambda s: slept.append(s))

    response = Client("t", "k").get("/x", retries=1)

    assert slept == [7.0], "honour Retry-After rather than guessing"
    assert response.status == 429


def test_non_json_body_does_not_crash_the_watch(monkeypatch):
    """Gateways return HTML error pages; that must not end a four-hour run."""

    class Html:
        status_code = 502
        headers = {}
        text = "<html>bad gateway</html>"

        def json(self):
            raise ValueError("not json")

    monkeypatch.setattr(requests.Session, "get", lambda *a, **k: Html())

    response = Client("t", "k").get("/x", retries=0)

    assert response.status == 502
    assert response.body == "<html>bad gateway</html>"
    assert response.reason is None, "a string body must not be treated as a dict"


def test_a_502_between_two_good_polls_is_reported_and_recovered_from():
    state = PathState("/x")
    state.observe(resp(200, {"fame": 1}))
    outage = state.observe(resp(502, "<html>"))
    recovery = state.observe(resp(200, {"fame": 2}))

    assert [e["kind"] for e in outage] == ["status_change"]
    kinds = [e["kind"] for e in recovery]
    assert "status_change" in kinds and "field_change" in kinds, (
        "state must survive a 502 so the recovery diff is still possible"
    )


def test_repeated_identical_polls_emit_nothing():
    """The signal is transitions. A quiet training day must stay quiet."""
    state = PathState("/x")
    state.observe(resp(200, {"fame": 1}))

    for _ in range(50):
        assert state.observe(resp(200, {"fame": 1})) == []


def test_a_huge_diff_is_capped_so_one_poll_cannot_flood_the_stream():
    """A war day changes hundreds of participant fields; that is noise."""
    state = PathState("/x")
    before = {"participants": [{"tag": f"#{n}", "decks": 0} for n in range(200)]}
    after = {"participants": [{"tag": f"#{n}", "decks": 4} for n in range(200)]}
    state.observe(resp(200, before))

    events = state.observe(resp(200, after))

    assert len(events) <= 41
    assert any(e["kind"] == "field_change_overflow" for e in events)


def test_a_large_replacement_value_is_summarised_not_pasted():
    """An event line is for reading; it must not paste an entire roster."""
    state = PathState("/x")
    state.observe(resp(200, {"roster": {"a": 1}}))

    (event,) = [e for e in state.observe(resp(200, {"roster": list(range(500))}))
                if e["kind"] == "field_change"]

    assert isinstance(event["to"], str) and "len 500" in event["to"]


def test_list_growth_is_reported_per_item_and_capped():
    """A list gaining entries is real signal (a war log entry, a clan joining),
    but 499 of them is not — report some, then say how many were suppressed."""
    state = PathState("/x")
    state.observe(resp(200, {"roster": [1]}))

    events = state.observe(resp(200, {"roster": list(range(500))}))

    added = [e for e in events if e.get("change") == "added"]
    assert added, "list additions must not vanish into a contentless payload_change"
    assert len(events) <= 41
    assert any(e["kind"] == "field_change_overflow" for e in events)


def test_a_single_new_log_entry_is_visible():
    """The season-roll signal on riverracelog: items gains one entry."""
    state = PathState("/log")
    state.observe(resp(200, {"items": [{"seasonId": 135, "sectionIndex": 4}]}))

    events = state.observe(resp(200, {"items": [{"seasonId": 136, "sectionIndex": 0},
                                                {"seasonId": 135, "sectionIndex": 4}]}))

    assert any(e["kind"] == "field_change" for e in events)


def test_unicode_player_names_survive_the_round_trip(tmp_path):
    """Real rosters contain names like Ｓｈａｆｉｔｈ and £eoππe§§;"""
    store = Store(tmp_path / "c.db")
    name = "Ｓｈａｆｉｔｈ Ｎｉｈａｌ♥️ £eoππe§§; AHMOメŞΛDØW"
    store.record_request("s", "/p", resp(200, {"name": name}))

    sha = store.requests_for("s", "/p")[0]["sha256"]

    assert store.payload(sha)["name"] == name


def test_every_event_is_json_serialisable():
    """stdout is a machine interface; one unserialisable event breaks the stream."""
    state = PathState("/x")
    state.observe(resp(200, {"a": 1}))
    events = state.observe(resp(404, {"reason": "notFound"}))
    events += state.observe(resp(0, None, error="boom"))

    for event in events:
        json.loads(json.dumps(event, default=str))


def test_store_survives_being_reopened(tmp_path):
    """A recorder restarted mid-season must append, not clobber."""
    path = tmp_path / "c.db"
    first = Store(path)
    first.record_request("s", "/x", resp(200, {"a": 1}))
    first.close()

    second = Store(path)
    second.record_request("s", "/x", resp(200, {"a": 2}))

    assert len(second.requests_for("s", "/x")) == 2


@pytest.mark.parametrize(
    ("raw", "expected_fragment"),
    [
        ("/clans/#ABC", "/clans/%23ABC"),
        ("clans/#ABC", "/clans/%23ABC"),
        ("https://api.clashroyale.com/v1/clans/#ABC", "/clans/%23ABC"),
        ("/clans/#ABC/riverracelog?limit=2", "limit=2"),
        ("  /cards  ", "/cards"),
    ],
)
def test_paths_are_accepted_in_the_shapes_people_actually_type(raw, expected_fragment):
    assert expected_fragment in normalize_path(raw)


def test_query_string_is_not_mangled_by_tag_encoding():
    url = normalize_path("/clans/#ABC/riverracelog?limit=2&x=#y")
    assert "%23ABC" in url
    assert url.endswith("limit=2&x=#y"), "only the path is encoded, not the query"


def test_preset_names_the_tags_it_still_needs():
    """A four-hour recording that dies on a missing argument is worse than useless."""
    from crprobe.presets import resolve

    with pytest.raises(ValueError, match=r"--clan and --player"):
        resolve("season-roll", clan=None, player=None)

    with pytest.raises(ValueError, match=r"--player"):
        resolve("season-roll", clan="#ABC", player=None)

    paths, fields, interval = resolve("season-roll", clan="#ABC", player="#XYZ")
    assert any("%s" % "#ABC" in p for p in paths) and any("#XYZ" in p for p in paths)
    assert interval > 0 and fields


def test_war_day_preset_needs_only_a_clan():
    from crprobe.presets import resolve

    paths, _fields, _interval = resolve("war-day", clan="#ABC", player=None)
    assert paths == ["/clans/#ABC/currentriverrace"]
