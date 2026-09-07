# Observe a boundary (war week, and season)

Clash Royale's boundaries are unrepeatable. A war week rolls once a week and a season once a month, and when one passes
unobserved the next chance is a week or a month away. The September 2026 season roll was documented from a war-log
timestamp, two phone screenshots and a bot database, and the least precise figure in the resulting table came from a
screenshot.

`tools/cr-probe` exists so that never has to happen again. These are the prompts to run each time, and the open
questions each run should chip away at. They are written to be pasted as-is, every week and every season, until the
open-questions list below is empty.

## When

| Boundary          | When                                                 | Start recording by |
| ----------------- | ---------------------------------------------------- | ------------------ |
| **War week roll** | Every Monday that is NOT the first of the month      | 09:15 UTC          |
| **Season roll**   | First Monday of the month, season rolls 10:00:00 UTC | 09:15 UTC          |

The weekly race close drifts season to season (09:37 in S133, 09:30 in S134, 09:34 in S135) but is stable within a
season, so 09:15 UTC is early enough without guessing. Confirm the current season's close with
`crprobe survey week-close` rather than assuming last season's.

On a first Monday BOTH boundaries happen: the week closes ~09:34 and the season rolls at 10:00. Use the season prompt
that day — it covers both.

## The day before: pre-flight

A dead key at 09:15 costs a month. Run this the day before either boundary:

```sh
cd tools/cr-probe && uv sync && uv run crprobe keys --human && uv run pytest -q
```

Every key should say `works: yes` and the IP allowlist should include this machine. If nothing works from here, fix it
now, not at the boundary.

---

## Prompt A — war week roll (any non-first Monday)

```text
We are observing a Clash Royale WAR WEEK rollover today with crprobe
(~/Projects/clash-royale/cr-agent-api-docs/tools/cr-probe). This is a recurring exercise:
each run should reduce the open-questions list in
recipes/observe-a-boundary.md, and anything we learn goes into the docs.

Before the boundary:
1. Pre-flight: `uv run crprobe keys --human` and `uv run pytest -q`. If a key
   does not work from this machine, stop and tell me.
2. Establish the expected close time for the CURRENT season with
   `crprobe survey week-close --clan '#J2RGCRVG' --human`. Do not assume last
   season's time; it drifts between seasons.
3. Read the "war week" and "season rollover" sections of clans.md and
   models/river-race.md so you know what we currently claim. The point of the
   exercise is to confirm or contradict those claims.

Record it:
   crprobe record --preset season-roll --clan '#J2RGCRVG' \
     --player '#20JJJ2CCRU' --session <sYYY-wN> --interval 10 --for 3h
Start by 09:15 UTC. Use the season-roll preset even for a week roll: it watches
the race, the war log and a player profile together, and we do not yet know
which of them moves first at a WEEK boundary.

While it runs, do not poll by hand — that is what the recorder is for. When it
finishes, `crprobe timeline <session> --human`.

Answer the open questions listed under "War week roll" in
recipes/observe-a-boundary.md, in particular: does currentriverrace 404
between weeks the way it does between seasons, or does it roll straight from
one section to the next? That is the biggest unknown.

Then:
- Update clans.md / models/river-race.md with what was measured. Write bounds
  where you measured bounds; never a timestamp you did not observe.
- Tick off or refine the open questions you answered, and add any new one the
  run raised.
- Add any newly observed enum value or fact to
  tools/docs-build/scripts/validate-observed-enums.mjs.
- Run the docs build, commit and push.

Report what changed versus what we already documented. If everything matched,
say so plainly — a boring confirmation is a real result and should be recorded
as one.
```

---

## Prompt B — season roll (first Monday of the month)

```text
We are observing a Clash Royale SEASON rollover today with crprobe
(~/Projects/clash-royale/cr-agent-api-docs/tools/cr-probe). The season rolls at 10:00:00
UTC. This is a recurring exercise: each run should reduce the open-questions
list in recipes/observe-a-boundary.md, and anything we learn goes into the docs.

Before the boundary:
1. Pre-flight: `uv run crprobe keys --human` and `uv run pytest -q`. If a key
   does not work from this machine, stop and tell me.
2. Re-read "The season rollover, minute by minute" in clans.md. That table was
   built by hand in September 2026 and parts of it were estimated; this run is
   how we replace estimates with measurements.

Record it:
   crprobe record --preset season-roll --clan '#J2RGCRVG' \
     --player '#20JJJ2CCRU' --session <sNNN-roll> --interval 10 --for 4h
Start by 09:15 UTC. Four hours is not excessive: the gap between the season
rolling and the new race appearing was ~16 min in July, ~77 min in August and
~9 min in September, so it is not predictable.

While it runs, do not poll by hand. When it finishes:
   crprobe timeline <session> --human

Answer the open questions listed under "Season roll" in
recipes/observe-a-boundary.md. The headline one: what are the true bounds of
the 404 "Waiting for Clan War to start" window? Every figure we have for it so
far was estimated rather than measured.

Then:
- Update the minute-by-minute table in clans.md with measured bounds, and add
  this season's row to the gap-length table.
- Check the war-week close time against the previous season: did it drift?
- Tick off or refine the open questions, and add any new one the run raised.
- Add any newly observed enum value or fact to
  tools/docs-build/scripts/validate-observed-enums.mjs.
- Run the docs build, commit and push.

Also worth checking, because these are downstream of the season id and have
been wrong before: does Elixir MCP's war_current report the new season with a
sensible section index, and does elixir-bot close the season and grant awards?
Report anything that disagrees.
```

---

## Open questions

Living list. Tick items off as runs answer them, and add what each run raises. When this list is empty the boundary is
baked and these prompts can retire (or become a scheduled job).

### War week roll

- [ ] **Does `currentriverrace` 404 between weeks?** We know it does between seasons. Whether a plain week boundary has
      the same gap is unknown, and it changes how consumers should treat a 404 on any Monday.
- [ ] Does `periodIndex` step cleanly (6 → 7) across a week boundary, or reset?
- [ ] Does the new `riverracelog` entry appear before, with, or after the race itself changes?
- [ ] Does `clan.fame` reset to 0 at the boundary, or lag by a poll?
- [ ] `periodLogs` is documented as spanning the whole SEASON. Confirm it is NOT cleared at a week boundary.
- [ ] Is the week-close time stable within a season to the second? S135 varied 09:34:04-09:34:06 across five weeks;
      confirm the pattern in S136.
- [ ] Does `clanWarTrophies` update at the week close or at the next race?

### Season roll

- [ ] **True bounds of the 404 window.** Every figure we have (~16 min July, ~77 min August, ~9 min September) was
      inferred, not measured.
- [ ] Is the season roll exactly 10:00:00Z every month, or does it drift like the week close does?
- [ ] What does `riverracelog` return during the 404 window — the closed season's final week, immediately?
- [ ] When does a player profile's previous-season / Path of Legend result flip relative to 10:00:00Z? In September it
      had already flipped by 09:45, i.e. BEFORE the season formally rolled.
- [ ] Does the first race of a season always appear at `sectionIndex 0`, `periodIndex 0`, `periodType training`?
- [ ] Does the week-close time drift at the season boundary specifically, or can it move mid-season?
- [ ] Is Pass Royale's season length always aligned to the war season?

### Answered

- [x] The week close and the season roll are two different events ~26 minutes apart (2026-09-07). Documented in
      clans.md.
- [x] The season hour is 10:00:00Z, not the ~09:30 the week close suggested (2026-09-07, confirmed against the client's
      own countdown).
- [x] `currentriverrace` 404s between the season roll and the new race, while `GET /clans/{tag}` still returns 200
      (2026-09-07).
- [x] Colosseum weeks carry the epoch-zero `finishTime` sentinel on EVERY standings entry, rank 1 included (2026-09-07,
      10 weeks, 3 seasons).

## What "baked" looks like

Every open question answered, the minute-by-minute table in clans.md built from measured bounds rather than estimates,
and three consecutive seasons whose observations agree. At that point the recording can move to a scheduled job and
these prompts become a fallback for when something surprises us.
