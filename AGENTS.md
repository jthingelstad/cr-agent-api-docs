# Agent Guide

This repository is an agent-first reference for the public Clash Royale API.

> **This repo is the single source of truth, and it is meant to be edited.** It exists to accumulate hard-won, observed
> API behavior. When the live API surprises you, write it down here as part of the fix — that is the point of the repo,
> not a favour to it.
>
> **If you are reading this file from inside another project** (a `docs/cr-api-docs/` or similar folder), you are in a
> stale copy. Vendored copies drifted in both directions and have been removed; edit the checkout at
> `~/Projects/clash-royale/cr-agent-api-docs` (github `jthingelstad/cr-agent-api-docs`) instead, or your learning is stranded.

## Start Here

1. Read [index.md](index.md) for global API rules, response-shape patterns, pagination, errors, caching, and endpoint
   discovery.
2. Read the endpoint file for the route you are implementing.
3. Read [game-modes.md](game-modes.md) when interpreting player activity, battle logs, events, rankings, or side modes.
4. Read [wiki-api-crosswalk.md](wiki-api-crosswalk.md) when mapping a wiki/gameplay concept to API docs, or mapping an
   API field back to game context.
5. Read only the focused model file(s) in [models/](models/) needed for that route.
6. Use [data/endpoints.json](data/endpoints.json), [data/game-modes.json](data/game-modes.json), and
   [data/wiki-api-crosswalk.json](data/wiki-api-crosswalk.json) for machine-readable endpoint and gameplay routing.
7. **Before writing a new rule down, check it** — see [recipes/verify-a-claim.md](recipes/verify-a-claim.md).
   `tools/cr-probe` calls the live API, surveys a claim across every week the API remembers, and records a scheduled
   transition (a season roll, a week close) unattended. A pattern that looks certain after one observation is how a
   wrong rule gets published.
8. **To observe a war week or season boundary as it happens**, use
   [recipes/observe-a-boundary.md](recipes/observe-a-boundary.md). It carries the standing prompts for both, and the
   list of questions still open about those boundaries — boundaries are unrepeatable, so an unobserved one costs a week
   or a month.

## Important Rules

- All internal links must be relative. Do not add filesystem-specific absolute links.
- Tags in path parameters start with `#` and must be URL-encoded as `%23`.
- Do not assume `{ items: [...] }` means pagination. Presence of `paging` is the reliable signal.
- Optional fields are usually absent, not present as `null`.
- Nullable fields are explicitly called out where observed.
- Treat endpoints marked broken, disabled, removed, or undocumented as operational constraints.
- Do not equate all activity with Trophy Road. Ranked / Path of Legend, Clan Wars, events, tournaments, 2v2, and side
  modes have distinct API signals.
- Do not add notes about specific downstream consumers of this repo.
- Prefer a measurement to a memory. State what was observed, when, and against which clan or player; say "observed
  August 2026", not "usually".
- Where a value was bounded rather than measured exactly — anything derived from polling — write the bounds. Claiming a
  precision you did not measure is guessing with a timestamp on it.
- When you add an observed enum value or a specific fact, add it to
  `tools/docs-build/scripts/validate-observed-enums.mjs` so a later rewrite cannot quietly drop it.

## Official Docs Comparison

The official Swagger UI is a useful baseline, but observed live API behavior is higher-confidence when the two conflict.
Keep both signals explicit instead of silently replacing one with the other.

The official Swagger UI currently lists these endpoint groups:

- `clans`
- `players`
- `cards`
- `tournaments`
- `locations`
- `events`
- `leaderboards`
- `globaltournaments`

The local [challenges.md](challenges.md) file documents historical/observed behavior for an endpoint that is not
currently shown in the official Swagger UI.
