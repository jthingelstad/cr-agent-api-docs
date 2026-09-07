# crprobe

Observe, watch and record the live Clash Royale API, so what goes into these docs is measured rather than remembered.

It lives here rather than in its own repo because it is one loop with the reference: `survey` produces the evidence
tables in the docs, and `tools/docs-build/scripts/validate-observed-enums.mjs` guards those same values in CI.
Verification has to be cheaper than guessing, or it stops happening.

## Running it

```sh
cd tools/cr-probe
uv sync
uv run crprobe --help
```

Output is agent-first: JSON on stdout, diagnostics on stderr, so everything pipes into `jq`. Add `-H/--human` for
tables. (`-h` is `--help`; taking it for `--human` would be a nasty surprise.)

## Keys

You do not tell it the variable name. Point it at whatever file the thing you are debugging uses and it works out which
value is the key:

```sh
uv run crprobe keys --key-file ~/Projects/elixir-mcp/.env --human
```

Supercell keys are JWTs, so a candidate is identified by its claims rather than guessed from its name; other services'
secrets are ruled out, and a live call is the final arbiter. Key values are never printed or stored — candidates are
reported as `file:VARNAME`.

`keys` also reports the token's IP allowlist against this machine's address, which answers the question that wastes the
most time here: **is the key wrong, or is it simply allowlisted for a different network?** A `403` with an IP in the
message means the latter.

## Commands

| Command    | What it is for                                                       |
| ---------- | -------------------------------------------------------------------- |
| `keys`     | Which keys exist, whether they work from here, and their IP binding  |
| `get`      | One call, raw JSON. Tags may be written as `#ABC` and are encoded    |
| `watch`    | Poll endpoints, print only what changed                              |
| `record`   | Watch a preset unattended and archive every request and payload      |
| `timeline` | Reconstruct a recorded session into something you can paste in a doc |
| `sessions` | List captures                                                        |
| `survey`   | Check a documented claim against every week the API remembers        |

## The season rollover

This is what the tool was built for. The September 2026 roll was documented by hand from a war-log timestamp, two
screenshots, a bot database and an MCP tool, and the least precise figure in the resulting table is the one that came
from a screenshot.

Start it before the boundary — first Monday of the month, 10:00 UTC — and walk away:

```sh
uv run crprobe record --preset season-roll \
  --clan '#J2RGCRVG' --player '#20JJJ2CCRU' \
  --session s137-roll --interval 10 --for 4h
uv run crprobe timeline s137-roll --human
```

The preset watches the race, the war log and a player profile together, because the boundary shows up at different
minutes in each: the race stops resolving, the log gains an entry, and the profile's `previousSeason` flips.

Transitions are reported as **windows, not instants**. A 10s poll cannot know when a 404 began, only that it began
between two observations, so every transition carries `between` bounds and every window a duration range. Failed polls
are recorded as `poll_error` rather than passing silently, because a gap in observation must never read as "nothing
happened".

## Checking a claim before you write it

```sh
uv run crprobe survey finish-time --clan '#J2RGCRVG' --human
uv run crprobe survey week-close --clan '#J2RGCRVG' --human
```

`finish-time` exists because the Colosseum sentinel rule looked obvious after one week and only became trustworthy after
ten. `week-close` shows the weekly race close is stable within a season and drifts between them — the distinction that a
phantom season came from conflating.

## Captures

`captures/crprobe.db` (SQLite, gitignored). Every request and payload, with payloads content-addressed and deduplicated
— polling every 10s yields mostly identical bodies.

**This repo is public.** Captures hold real player tags and names, including opponents. They are gitignored by default;
`--redact` replaces identity with stable pseudonyms so a capture can be cited as evidence without publishing people.
Redaction is stable, so a repeated player is still visibly the same player.
