"""Change detection, and the honesty about precision that is the point of it."""

from crprobe.client import Response, normalize_path
from crprobe.events import PathState, redact_payload


def resp(status=200, body=None, error=None):
    return Response(status, body, 12, "https://example/x", "test/.env:K", error)


def test_tag_sigil_survives_url_building():
    """'#' is the tag marker, not a fragment. Losing it silently queries the clan list."""
    assert normalize_path("/clans/#20JJJ2CCRU/currentriverrace").endswith(
        "/clans/%2320JJJ2CCRU/currentriverrace"
    )


def test_already_encoded_tags_are_not_double_encoded():
    assert "%2523" not in normalize_path("/clans/%2320JJJ2CCRU")


def test_first_observation_reports_a_baseline_not_a_change():
    state = PathState("/x")
    events = state.observe(resp(200, {"a": 1}))
    assert [e["kind"] for e in events] == ["status_change"]
    assert events[0]["from"] is None


def test_status_change_carries_bounds_not_a_false_exact_time():
    """A 5s poll cannot know when a 404 began, only that it began between polls."""
    state = PathState("/x")
    state.observe(resp(200, {"a": 1}))
    first_seen = state.last_seen_at

    events = state.observe(resp(404, {"reason": "notFound"}))

    change = next(e for e in events if e["kind"] == "status_change")
    assert change["between"]["after"] == first_seen
    assert change["between"]["by"] == state.last_seen_at
    assert change["between"]["after"] != change["between"]["by"]


def test_the_between_races_404_is_explained_not_just_reported():
    state = PathState("/x")
    state.observe(resp(200, {"a": 1}))
    change = next(e for e in state.observe(resp(404, {"reason": "notFound"}))
                  if e["kind"] == "status_change")
    assert "not a deleted clan" in change["note"]


def test_scalar_change_is_reported_with_old_and_new():
    state = PathState("/x")
    state.observe(resp(200, {"clan": {"fame": 100}}))

    events = state.observe(resp(200, {"clan": {"fame": 300}}))

    change = next(e for e in events if e["kind"] == "field_change")
    assert change["field"] == "clan.fame"
    assert (change["from"], change["to"]) == (100, 300)


def test_field_filter_suppresses_battle_day_churn():
    state = PathState("/x", fields=("clan.fame",))
    state.observe(resp(200, {"clan": {"fame": 1}, "participants": [{"decks": 1}]}))

    events = state.observe(resp(200, {"clan": {"fame": 2}, "participants": [{"decks": 4}]}))

    fields = [e["field"] for e in events if e["kind"] == "field_change"]
    assert fields == ["clan.fame"]


def test_a_failed_poll_is_recorded_rather_than_looking_like_no_change():
    """A silent gap would let a timeline claim a window it never observed."""
    state = PathState("/x")
    state.observe(resp(200, {"a": 1}))

    events = state.observe(resp(0, None, error="connection reset"))

    assert any(e["kind"] == "poll_error" for e in events)


def test_redaction_is_stable_so_repeat_players_stay_linkable():
    payload = {"participants": [{"tag": "#ABC", "name": "Real Name", "fame": 5},
                                {"tag": "#ABC", "name": "Real Name", "fame": 5}]}

    out = redact_payload(payload)

    first, second = out["participants"]
    assert first["tag"] == second["tag"]
    assert first["tag"].startswith("#REDACT")
    assert second["name"].startswith("redacted-")
    assert "Real Name" not in str(out)
    assert first["fame"] == 5, "redaction must not damage the data being studied"
