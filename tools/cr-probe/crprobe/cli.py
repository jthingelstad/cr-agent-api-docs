"""crprobe -- observe the live Clash Royale API so findings become fact.

Output is agent-first: JSON to stdout, everything else to stderr, so any
command pipes into jq or a script. `-H/--human` renders the same data as
tables for a person. (`-h` is argparse/click's help; taking it for --human
would be a nasty surprise.)
"""

from __future__ import annotations

import json
import signal
import sys
import time
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from . import survey as survey_mod
from . import timeline as timeline_mod
from .client import Client, public_ip
from .credentials import discover
from .events import PathState, redact_payload
from .presets import PRESETS, resolve
from .store import Store, utcnow

err = Console(stderr=True)
out = Console()


def _emit(record: dict, human: bool) -> None:
    """One event, one line of JSON — or a readable line for a person."""
    if not human:
        click.echo(json.dumps(record, default=str))
        return
    kind = record.get("kind", "?")
    at = (record.get("at") or "")[11:23]
    if kind == "status_change":
        colour = "red" if record.get("to") != 200 else "green"
        err.print(f"[dim]{at}[/dim] [{colour}]{record['from']} -> {record['to']}[/{colour}] "
                  f"{record['path']}" + (f"  [yellow]{record['note']}[/yellow]" if record.get("note") else ""))
    elif kind == "field_change":
        err.print(f"[dim]{at}[/dim] [cyan]{record['field']}[/cyan] "
                  f"{record.get('from')!r} -> {record.get('to')!r}  [dim]{record['path']}[/dim]")
    elif kind == "poll_error":
        err.print(f"[dim]{at}[/dim] [red]poll failed[/red] {record['path']}: {record.get('error')}")
    else:
        err.print(f"[dim]{at}[/dim] {kind} {record.get('path','')}")


def _client(key_file: tuple[str, ...], key_name: str | None, *, quiet: bool = False) -> Client:
    """Pick a working credential, saying which one — never what it is."""
    candidates = discover(tuple(key_file), name=key_name)
    if not candidates:
        raise click.ClickException(
            "no API key found. Pass --key-file pointing at a .env (or any file) "
            "that holds one; the variable name does not matter."
        )
    problems = []
    for candidate in candidates:
        client = Client(candidate.value, candidate.label)
        probe = client.get("/cards", retries=0)
        if probe.ok:
            if not quiet:
                err.print(f"[dim]key: {candidate.label}[/dim]")
            return client
        problems.append(f"{candidate.label}: {probe.status} {probe.reason or probe.error or ''}".strip())
        client.close()
    raise click.ClickException("no candidate key worked:\n  " + "\n  ".join(problems))


key_options = [
    click.option("--key-file", multiple=True, type=click.Path(),
                 help="File holding an API key. The variable name is detected; "
                      "repeatable. Point it at the .env of whatever you are debugging."),
    click.option("--key-name", default=None,
                 help="Use only this variable name, when a file holds several."),
]


def with_key_options(fn):
    for option in reversed(key_options):
        fn = option(fn)
    return fn


@click.group(context_settings={"help_option_names": ["--help"]})
@click.version_option("0.1.0", prog_name="crprobe")
def main() -> None:
    """Observe, watch and record the live Clash Royale API.

    JSON goes to stdout and diagnostics to stderr, so every command pipes.
    """


@main.command()
@with_key_options
@click.option("-H", "--human", is_flag=True, help="Readable tables instead of JSON.")
def keys(key_file, key_name, human):
    """Show which API keys were found and whether they work from here.

    Answers the question that wastes the most time with this API: is the key
    wrong, or is it simply allowlisted for a different network?
    """
    candidates = discover(tuple(key_file), name=key_name)
    if not candidates:
        raise click.ClickException("no candidate keys found")
    ip = public_ip()
    rows = []
    for candidate in candidates:
        client = Client(candidate.value, candidate.label)
        probe = client.get("/cards", retries=0)
        client.close()
        permitted = candidate.permits_ip(ip)
        rows.append({
            "key": candidate.label,
            "jwt": candidate.is_jwt,
            "issuer": candidate.issuer,
            "allowlisted_cidrs": candidate.allowed_cidrs or None,
            "our_ip_allowed": permitted,
            "status": probe.status,
            "works": probe.ok,
            "note": ("allowlisted for another network" if probe.is_invalid_ip else probe.reason),
        })
    if human:
        table = Table(title=f"API keys (this machine: {ip or 'unknown IP'})")
        for column in ("key", "works", "status", "issuer", "IP allowed", "note"):
            table.add_column(column, overflow="fold")
        for row in rows:
            table.add_row(row["key"], "yes" if row["works"] else "no", str(row["status"]),
                          str(row["issuer"] or "-"),
                          {True: "yes", False: "NO", None: "-"}[row["our_ip_allowed"]],
                          str(row["note"] or ""))
        out.print(table)
    else:
        click.echo(json.dumps({"public_ip": ip, "keys": rows}, indent=2))


@main.command()
@click.argument("path")
@click.option("--query", multiple=True, help="Extra query parameter, k=v. Repeatable.")
@with_key_options
@click.option("-H", "--human", is_flag=True, help="Pretty-print instead of raw JSON.")
def get(path, query, key_file, key_name, human):
    """Call one endpoint and print the JSON body.

    Tags may be written naturally: '#20JJJ2CCRU' is encoded for you.
    """
    client = _client(key_file, key_name)
    if query:
        joined = "&".join(query)
        path = f"{path}{'&' if '?' in path else '?'}{joined}"
    response = client.get(path)
    err.print(f"[dim]{response.status} {response.url} {response.elapsed_ms}ms[/dim]")
    if not response.ok:
        err.print(f"[red]{response.reason or response.error or 'failed'}[/red]")
        if response.is_invalid_ip:
            err.print("[yellow]this key is allowlisted for a different network; "
                      "try --key-file for the host that owns it[/yellow]")
    if human:
        out.print_json(json.dumps(response.body, default=str))
    else:
        click.echo(json.dumps(response.body, indent=2, default=str))
    sys.exit(0 if response.ok else 1)


@main.command()
@click.argument("paths", nargs=-1, required=True)
@click.option("--interval", default=5.0, show_default=True, help="Seconds between polls.")
@click.option("--for", "duration", default=60.0, show_default=True,
              help="Seconds to watch. Use 0 to run until interrupted.")
@click.option("--field", multiple=True,
              help="Only report changes whose path contains this. Repeatable.")
@with_key_options
@click.option("-H", "--human", is_flag=True)
def watch(paths, interval, duration, field, key_file, key_name, human):
    """Poll endpoints and print only what changed.

    Transitions carry `between` bounds rather than a single timestamp: a 5s
    poll cannot know when a change happened, only that it happened between two
    observations.
    """
    client = _client(key_file, key_name)
    states = {p: PathState(p, fields=tuple(field)) for p in paths}
    _run_loop(client, states, interval, duration, human, store=None, session=None)


@main.command()
@click.option("--preset", type=click.Choice(sorted(PRESETS)), default="season-roll",
              show_default=True)
@click.option("--clan", default=None, help="Clan tag for presets that need one.")
@click.option("--player", default=None, help="Player tag for presets that need one.")
@click.option("--path", "extra_paths", multiple=True, help="Additional endpoint to watch.")
@click.option("--session", required=True, help="Name for this capture, e.g. s136-roll.")
@click.option("--interval", default=None, type=float, help="Override the preset's interval.")
@click.option("--for", "duration", default=0.0,
              help="Seconds to record; 0 runs until interrupted.")
@click.option("--redact", is_flag=True,
              help="Pseudonymise player and clan identity in stored payloads.")
@click.option("--db", type=click.Path(), default=None, help="Capture database path.")
@with_key_options
@click.option("-H", "--human", is_flag=True)
def record(preset, clan, player, extra_paths, session, interval, duration, redact,
           db, key_file, key_name, human):
    """Watch a preset unattended and archive every request and payload.

    Built for the monthly season roll: start it before the boundary, walk away,
    and read the timeline afterwards instead of reconstructing one from
    screenshots.
    """
    try:
        paths, fields, suggested = resolve(preset, clan=clan, player=player)
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    paths = list(paths) + list(extra_paths)
    if not paths:
        raise click.ClickException("nothing to watch: give --path or use a preset with endpoints")

    client = _client(key_file, key_name)
    store = Store(Path(db) if db else None)
    states = {p: PathState(p, fields=tuple(fields)) for p in paths}
    err.print(f"[dim]recording session '{session}' -> {store.path}[/dim]")
    for path in paths:
        err.print(f"[dim]  watching {path}[/dim]")
    _run_loop(client, states, interval or suggested, duration, human,
              store=store, session=session, redact=redact_payload if redact else None)
    err.print(f"[dim]session '{session}' saved. crprobe timeline {session}[/dim]")


def _run_loop(client, states, interval, duration, human, *, store, session, redact=None):
    """Poll on a fixed cadence until the clock runs out or the user stops us.

    Sleep is measured from the START of each cycle, not the end. Sleeping a
    flat `interval` after the work makes the real period `interval + cycle`,
    which drifts: over a four-hour record that is both fewer polls than asked
    for and less uniform bounds on every transition, and bound precision is the
    whole point of the exercise.
    """
    started = time.monotonic()
    behind = 0

    # An unattended record is stopped by SIGTERM, not Ctrl-C: launchd, a
    # `kill`, a shell that backgrounded it (and so set SIGINT to ignore).
    # Translate it into the same graceful path so the session is closed and
    # reported rather than truncated mid-cycle.
    def _stop(_signum, _frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, _stop)
    except (ValueError, OSError):
        # Not on the main thread; the default disposition still applies.
        pass

    try:
        while True:
            cycle_started = time.monotonic()
            for path, state in states.items():
                response = client.get(path)
                if store is not None:
                    store.record_request(session, path, response, redact=redact)
                for event in state.observe(response):
                    _emit(event, human)
                    if store is not None:
                        store.record_event(session, path, event["kind"], event)
                    sys.stdout.flush()
            if duration and (time.monotonic() - started) >= duration:
                break
            remaining = interval - (time.monotonic() - cycle_started)
            if remaining <= 0:
                # Polling slower than requested. Say so once rather than
                # silently producing a coarser record than the operator thinks.
                behind += 1
                if behind == 1:
                    err.print(f"[yellow]cycle takes longer than --interval {interval}s; "
                              f"polling as fast as it can[/yellow]")
                continue
            time.sleep(remaining)
    except KeyboardInterrupt:
        err.print("\n[dim]stopped[/dim]")


@main.command("timeline")
@click.argument("session")
@click.option("--db", type=click.Path(), default=None)
@click.option("--fields/--no-fields", default=True, help="Include field-level changes.")
@click.option("-H", "--human", is_flag=True)
def timeline_cmd(session, db, fields, human):
    """Reconstruct what happened during a recorded session.

    Prints the transitions and the non-200 windows with honest bounds — ready
    to become a docs table.
    """
    store = Store(Path(db) if db else None)
    events = store.events(session)
    if not events:
        raise click.ClickException(f"no events recorded for session '{session}'")
    rows = timeline_mod.build(events, include_fields=fields)
    spans = timeline_mod.windows(events)
    if human:
        table = Table(title=f"session {session}: {len(rows)} transition(s)")
        for column in ("time", "kind", "path", "detail"):
            table.add_column(column, overflow="fold")
        for row in rows:
            detail = (f"{row.get('from')} -> {row.get('to')}" if row["kind"] == "status_change"
                      else f"{row.get('field','')} {row.get('from','')} -> {row.get('to','')}")
            table.add_row((row.get("at") or "")[11:23], row["kind"], row.get("path", ""), detail.strip())
        out.print(table)
        if spans:
            window_table = Table(title="non-200 windows")
            for column in ("path", "status", "began after", "began by", "ended by", "duration"):
                window_table.add_column(column, overflow="fold")
            for span in spans:
                bounds = span.get("duration_bounds") or {}
                length = (f"{bounds.get('at_least_seconds')}-{bounds.get('at_most_seconds')}s"
                          if bounds else "open")
                window_table.add_row(span["path"], str(span["status"]),
                                     str(span.get("began_after")), str(span.get("began_by")),
                                     str(span.get("ended_by")), length)
            out.print(window_table)
    else:
        click.echo(json.dumps({"session": session, "transitions": rows, "windows": spans},
                              indent=2, default=str))


@main.command("sessions")
@click.option("--db", type=click.Path(), default=None)
@click.option("-H", "--human", is_flag=True)
def sessions_cmd(db, human):
    """List recorded capture sessions."""
    store = Store(Path(db) if db else None)
    rows = store.sessions()
    if human:
        table = Table(title=f"captures in {store.path}")
        for column in ("session", "requests", "started", "ended"):
            table.add_column(column)
        for row in rows:
            table.add_row(row["session"], str(row["requests"]), row["started"], row["ended"])
        out.print(table)
    else:
        click.echo(json.dumps(rows, indent=2, default=str))


@main.command("survey")
@click.argument("name", type=click.Choice(sorted(survey_mod.SURVEYS)))
@click.option("--clan", required=True, help="Clan tag to survey.")
@click.option("--limit", default=10, show_default=True, help="Weeks of river race log.")
@with_key_options
@click.option("-H", "--human", is_flag=True)
def survey_cmd(name, clan, limit, key_file, key_name, human):
    """Check a documented claim against every week the API remembers.

    Use this before writing a rule down. A pattern that looks certain after one
    week is how a wrong rule gets published.
    """
    client = _client(key_file, key_name)
    result = survey_mod.SURVEYS[name](client, clan, limit)
    if result.get("error"):
        raise click.ClickException(result["error"])
    if human:
        if "holds" in result:
            verdict = "[green]HOLDS[/green]" if result["holds"] else "[red]DOES NOT HOLD[/red]"
            out.print(f"{result['claim']}\n  {verdict} across {result['weeks']} week(s)")
        table = Table(title=name)
        for column in (result["rows"][0].keys() if result["rows"] else []):
            table.add_column(column, overflow="fold")
        for row in result["rows"]:
            table.add_row(*[str(v) for v in row.values()])
        out.print(table)
    else:
        click.echo(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
