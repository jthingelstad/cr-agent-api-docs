"""The polling loop: cadence, graceful stops, and not lying about coverage."""

from __future__ import annotations

import signal

import pytest

from crprobe import cli
from crprobe.client import Response
from crprobe.events import PathState


class FakeClient:
    def __init__(self, bodies):
        self._bodies = list(bodies)
        self.calls = 0

    def get(self, path, **kwargs):
        self.calls += 1
        body = self._bodies[min(self.calls - 1, len(self._bodies) - 1)]
        return Response(200, body, 1, path, "test:KEY")


def test_sigterm_is_wired_to_the_graceful_stop(monkeypatch):
    """Unattended runs are ended by SIGTERM, not Ctrl-C. If it is not handled
    the session is truncated mid-cycle instead of closed and reported."""
    registered = {}
    monkeypatch.setattr(signal, "signal",
                        lambda sig, handler: registered.__setitem__(sig, handler))
    monkeypatch.setattr(cli.time, "sleep", lambda _s: None)
    client = FakeClient([{"a": 1}])
    states = {"/x": PathState("/x")}

    cli._run_loop(client, states, 0.01, 0.01, False, store=None, session=None)

    assert signal.SIGTERM in registered
    with pytest.raises(KeyboardInterrupt):
        registered[signal.SIGTERM](signal.SIGTERM, None)


def test_sleep_is_measured_from_the_start_of_the_cycle(monkeypatch):
    """Sleeping a flat interval AFTER the work makes the real period
    interval+cycle, which drifts and widens every transition bound."""
    slept: list[float] = []
    clock = {"t": 0.0}

    def fake_monotonic():
        clock["t"] += 0.4  # each call advances; the cycle "costs" time
        return clock["t"]

    monkeypatch.setattr(cli.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(cli.time, "sleep", lambda s: slept.append(s))
    monkeypatch.setattr(signal, "signal", lambda *a: None)
    client = FakeClient([{"a": 1}, {"a": 2}, {"a": 3}])
    states = {"/x": PathState("/x")}

    cli._run_loop(client, states, 5.0, 3.0, False, store=None, session=None)

    assert slept, "it must sleep between cycles"
    assert all(s < 5.0 for s in slept), "sleep must be reduced by the cycle's own cost"


def test_falling_behind_is_announced_not_silently_absorbed(monkeypatch, capsys):
    """A record that quietly polls slower than asked produces a coarser
    timeline than the operator believes they have."""
    monkeypatch.setattr(signal, "signal", lambda *a: None)
    monkeypatch.setattr(cli.time, "sleep", lambda _s: None)
    ticks = iter([0.0] + [i * 10.0 for i in range(1, 40)])
    monkeypatch.setattr(cli.time, "monotonic", lambda: next(ticks))
    client = FakeClient([{"a": 1}])
    states = {"/x": PathState("/x")}

    cli._run_loop(client, states, 0.5, 25.0, False, store=None, session=None)

    assert "longer than --interval" in capsys.readouterr().err


def test_a_zero_duration_run_still_polls_once(monkeypatch):
    """`--for 0` means run until stopped, not "do nothing"."""
    monkeypatch.setattr(signal, "signal", lambda *a: None)
    calls = {"n": 0}

    def sleep_then_stop(_s):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(cli.time, "sleep", sleep_then_stop)
    client = FakeClient([{"a": 1}])
    states = {"/x": PathState("/x")}

    cli._run_loop(client, states, 0.01, 0, False, store=None, session=None)

    assert client.calls >= 2, "duration 0 must keep polling until interrupted"
