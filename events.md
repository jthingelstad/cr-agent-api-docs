# Clash Royale API – Events Endpoints

Base URL: `https://api.clashroyale.com/v1` Auth: Bearer token in `Authorization` header

Gameplay context: use [game-modes.md](game-modes.md#event-and-challenge-variants) and
[wiki-api-crosswalk.md](wiki-api-crosswalk.md#events-challenges-and-temporary-modes) when interpreting active event
titles, event battle logs, and temporary rule variants.

---

## Endpoints

### GET /events

Get all current in-game events.

**Query:** None

**Returns:** bare JSON array of `TrailEvent` objects (NOT wrapped in `{ items: [...] }`)

**TrailEvent shape:**

```json
{ "eventTag": "#R8U2RCJ", "title": "C.H.A.O.S", "description": "Choose different modifiers during battle..." }
```

| Field         | Type             | Notes                                                                            |
| ------------- | ---------------- | -------------------------------------------------------------------------------- |
| `eventTag`    | string           | Identifies one run of an event, not the event (see Agent Notes), e.g. `#R8U2RCJ` |
| `title`       | string           | Localized event name                                                             |
| `description` | string, nullable | Localized event description — null for some events                               |

**Example response (observed March 2026; these tags have since turned over, see Agent Notes):**

```json
[
  { "eventTag": "#R8U2RCJ", "title": "C.H.A.O.S", "description": "Choose different modifiers during battle..." },
  { "eventTag": "#R8UJQUU", "title": "Classic 1v1", "description": "Play a good old-fashioned Battle..." },
  { "eventTag": "#R8UJR98", "title": "Classic 2v2", "description": "Play a classic game of 2v2!..." },
  { "eventTag": "#R8UJCCJ", "title": "Mega Draft Challenge", "description": "Each win in a Challenge..." },
  { "eventTag": "#R8UJV80", "title": "Classic Challenge", "description": "Each win in a Challenge..." },
  { "eventTag": "#R8UC0LP", "title": "Grand Challenge", "description": "Each win in a Challenge..." },
  { "eventTag": "#R8UURVL", "title": "Merge Tactics", "description": null }
]
```

---

## Error Codes

| Code | Meaning                                 |
| ---- | --------------------------------------- |
| 400  | Bad parameters                          |
| 403  | Auth failure / insufficient token scope |
| 404  | Not found                               |
| 429  | Rate limit exceeded                     |
| 500  | Server error                            |
| 503  | Maintenance                             |

Observed error bodies are usually `{ reason, message? }`. `type`/`detail` were not observed.

---

## Agent Notes

- Returns a **bare array**, not `{ items: [...] }` — this is one of two endpoints that do this (the other is
  `/players/{tag}/battlelog`)
- `title` and `description` are localized — locale is determined by the API token's configured region
- `description` can be null for some events (observed for "Merge Tactics")
- Returns only currently active events, not upcoming or historical
- Query params appear to be ignored — `/events?limit=5` still returned the full bare array in March 2026 testing
- `eventTag` values appear in battle log entries (`Battle.eventTag`) — can be used to cross-reference which event a
  battle was played in
- **`eventTag` identifies one run of an event, not the event.** Always-on events keep their title but get a new tag as
  runs turn over: of seven titles present in every capture June-September 2026, four changed tag at least once, with
  three of them changing together about once a month. None of the March 2026 example tags above appeared in those
  captures. Join battles to `/events` on the tag, but track an event over time by title.
- Seven events were in every one of 26 captures, June to September 2026: Classic 1v1, Classic 2v2, Classic Challenge,
  Grand Challenge, Mega Draft Challenge, Merge Tactics and Seasonal Trophy Road. Everything else rotated one to three at
  a time, so a capture averaged 8.6 entries. Rotating titles observed include the C.H.A.O.S run
  (`C.H.A.O.S (Phase 1)`-`(Phase 3)`, `C.H.A.O.S Draft`, `C.H.A.O.S Triple Draft`, `C.H.A.O.S Infinite Elixir`,
  `C.H.A.O.S Sudden Death`, `C.H.A.O.S Epic Only`, July-September 2026), `2v2 League`, `Royale Shuffle`,
  `Princess Gambit Tournament`, `Bare Bones Tournament` and `Restless Undead`.
