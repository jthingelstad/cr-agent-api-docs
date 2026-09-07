"""Timeline reconstruction: the output that should become a docs table."""

from crprobe import timeline


def status(path, frm, to, after, by):
    return {"kind": "status_change", "path": path, "from": frm, "to": to,
            "at": by, "between": {"after": after, "by": by}}


A = "2026-10-05T09:59:55.000000Z"
B = "2026-10-05T10:00:10.000000Z"
C = "2026-10-05T10:08:55.000000Z"
D = "2026-10-05T10:09:10.000000Z"


def test_window_keeps_both_bounds_instead_of_inventing_a_timestamp():
    events = [status("/race", 200, 404, A, B), status("/race", 404, 200, C, D)]

    (window,) = timeline.windows(events)

    assert window["began_after"] == A and window["began_by"] == B
    assert window["ended_after"] == C and window["ended_by"] == D


def test_duration_is_a_range_because_polling_bounds_it():
    events = [status("/race", 200, 404, A, B), status("/race", 404, 200, C, D)]

    bounds = timeline.windows(events)[0]["duration_bounds"]

    # Shortest: last-404-poll minus first-404-poll. Longest: outer bounds.
    assert bounds["at_least_seconds"] == 525
    assert bounds["at_most_seconds"] == 555
    assert bounds["at_least_seconds"] < bounds["at_most_seconds"]


def test_a_window_still_open_is_reported_rather_than_dropped():
    events = [status("/race", 200, 404, A, B)]

    (window,) = timeline.windows(events)

    assert window["status"] == 404
    assert "ended_by" not in window


def test_field_changes_can_be_excluded_for_a_summary_view():
    events = [status("/race", 200, 404, A, B),
              {"kind": "field_change", "path": "/race", "at": B, "field": "clan.fame"}]

    assert len(timeline.build(events, include_fields=True)) == 2
    assert len(timeline.build(events, include_fields=False)) == 1


def test_poll_errors_survive_into_the_timeline():
    """A gap in observation must be visible, or the timeline overstates what we saw."""
    events = [{"kind": "poll_error", "path": "/race", "at": B, "error": "timeout"}]

    assert timeline.build(events)[0]["kind"] == "poll_error"
