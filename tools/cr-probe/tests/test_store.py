"""The capture archive: dedup, and keeping evidence retrievable."""

from crprobe.client import Response
from crprobe.events import redact_payload
from crprobe.store import Store


def resp(body, status=200):
    return Response(status, body, 5, "https://example/x", "test/.env:K")


def test_identical_payloads_are_stored_once(tmp_path):
    """Polling every 5s produces mostly identical bodies; storing each would
    bury the moments that actually differ."""
    store = Store(tmp_path / "c.db")
    for _ in range(5):
        store.record_request("s1", "/race", resp({"fame": 100}))
    store.record_request("s1", "/race", resp({"fame": 200}))

    payloads = store._conn.execute("SELECT COUNT(*) FROM payload").fetchone()[0]
    requests = store._conn.execute("SELECT COUNT(*) FROM request").fetchone()[0]

    assert requests == 6, "every call is still recorded"
    assert payloads == 2, "but only distinct bodies are kept"


def test_requests_are_retrievable_in_order(tmp_path):
    store = Store(tmp_path / "c.db")
    store.record_request("s1", "/race", resp({"a": 1}))
    store.record_request("s1", "/race", resp(None, status=404))

    rows = store.requests_for("s1", "/race")

    assert [r["status"] for r in rows] == [200, 404]


def test_redaction_applies_to_what_is_written_to_disk(tmp_path):
    """The archive lives in a public repo's tree; a redacted capture must not
    contain the real identity anywhere."""
    store = Store(tmp_path / "c.db")
    store.record_request("s1", "/race", resp({"tag": "#REAL", "name": "Real Person"}),
                         redact=redact_payload)

    stored = store._conn.execute("SELECT body_json FROM payload").fetchone()[0]

    assert "#REAL" not in stored
    assert "Real Person" not in stored


def test_events_round_trip_for_the_timeline(tmp_path):
    store = Store(tmp_path / "c.db")
    store.record_event("s1", "/race", "status_change",
                       {"at": "2026-10-05T10:00:00.000000Z", "from": 200, "to": 404})

    (event,) = store.events("s1")

    assert event["kind"] == "status_change" and event["to"] == 404
