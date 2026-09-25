# Clash Royale API – Locations Endpoints

Base URL: `https://api.clashroyale.com/v1` Auth: Bearer token in `Authorization` header Tag encoding: `#2ABC` →
`%232ABC` in path

Gameplay context: use [game-modes.md](game-modes.md#ranked--path-of-legend) and
[wiki-api-crosswalk.md](wiki-api-crosswalk.md#progression-and-rewards) when separating Trophy Road rankings from Ranked
/ Path of Legend, clan, war, and tournament rankings.

---

## Endpoints

### GET /locations

List all available locations (regions + countries).

**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `{ items: [...], paging: { cursors: { ... } } }`

**Location shape:**

```json
{ "id": 57000249, "name": "United States", "isCountry": true, "countryCode": "US" }
```

Locations include both regions (continents) and countries:

- Regions: `{ id: 57000000, name: "Europe", isCountry: false }` — no `countryCode`
- Countries: `{ id: 57000249, name: "United States", isCountry: true, countryCode: "US" }`
- Special: `{ id: 57000006, name: "International", isCountry: false }`

262 total locations (8 regions + 254 countries). All IDs in range 57000000-57000261.

**Region IDs:**

| ID       | Name          |
| -------- | ------------- |
| 57000000 | Europe        |
| 57000001 | North America |
| 57000002 | South America |
| 57000003 | Asia          |
| 57000004 | Oceania       |
| 57000005 | Africa        |
| 57000006 | International |
| 57000261 | Unknown       |

**Common country IDs:**

| ID       | Name           | Code |
| -------- | -------------- | ---- |
| 57000021 | Australia      | AU   |
| 57000038 | Brazil         | BR   |
| 57000047 | Canada         | CA   |
| 57000056 | China          | CN   |
| 57000087 | France         | FR   |
| 57000094 | Germany        | DE   |
| 57000113 | India          | IN   |
| 57000120 | Italy          | IT   |
| 57000122 | Japan          | JP   |
| 57000153 | Mexico         | MX   |
| 57000193 | Russia         | RU   |
| 57000216 | South Korea    | KR   |
| 57000218 | Spain          | ES   |
| 57000248 | United Kingdom | GB   |
| 57000249 | United States  | US   |

---

### GET /locations/{locationId}

Get a single location by ID.

**Path:** `locationId` (required, integer)

**Returns:** `Location` object

```json
{ "id": 57000249, "name": "United States", "isCountry": true, "countryCode": "US" }
```

Note: No `localizedName` field was observed in responses. `countryCode` is absent for regions where `isCountry: false`.

---

## Location Rankings

### GET /locations/{locationId}/rankings/players

Get trophy leaderboard for players in a location.

**Path:** `locationId` (required) **Query:** `limit`, `after`, `before`

**Returns:** `{ items: [...], paging: { ... } }`

Note: May return an empty `items` array, early in a season and late in one (below).

Observed 2026-09-10 (day 3 of S136, which rolled 2026-09-07 10:00Z): `global` and `57000249` (United States) both
returned `items: []` with no paging cursors, while `/pathoflegend/players` for the same two locations returned 836 and
97 ranked players. Consistent with the seasonal trophy ranking endpoint being documented as broken below: treat the
trophy leaderboard as unavailable and use Path of Legend rankings for competitive standing. Do not write an empty
response through as "nobody is ranked". A read on 2026-09-05, two days before that roll, was also `items: []` with no
cursors (one archived read), so the emptiness is not an early-season effect alone.

---

### GET /locations/{locationId}/rankings/clans

Get trophy leaderboard for clans in a location.

**Path:** `locationId` (required) **Query:** `limit`, `after`, `before`

**Returns:** `{ items: [...], paging: { ... } }`

**ClanRanking shape:**

```json
{
  "tag": "#9LGR9PYY",
  "name": "War Knights",
  "rank": 1,
  "previousRank": 1,
  "location": { "id": 57000249, "name": "United States", "isCountry": true, "countryCode": "US" },
  "clanScore": 132637,
  "members": 50,
  "badgeId": 16000038
}
```

| Field          | Type     | Notes                              |
| -------------- | -------- | ---------------------------------- |
| `tag`          | string   | Clan tag                           |
| `name`         | string   |                                    |
| `rank`         | integer  | Current rank                       |
| `previousRank` | integer  | Previous rank (-1 if new/unranked) |
| `location`     | Location | Full location object               |
| `clanScore`    | integer  |                                    |
| `members`      | integer  | Member count                       |
| `badgeId`      | integer  |                                    |

---

### GET /locations/{locationId}/rankings/clanwars

Get clan war (river race) leaderboard for a location.

**Path:** `locationId` (required) **Query:** `limit`, `after`, `before`

**Returns:** Same shape as clan rankings. The `clanScore` here reflects river race/war performance, not overall
trophies.

**Both clan boards stop at 1,000 with no cursor.** At `limit=1000`, 48 reads per board across three locations
(2026-09-11 to 2026-09-25) averaged 999.3 clans, and every one returned `paging: { cursors: {} }`. This is the same cut
the Path of Legend board makes (below); an empty `cursors` here does not mean the location has no more clans.

---

### GET /locations/{locationId}/pathoflegend/players

Get Path of Legend player rankings for a location (current season).

**Path:** `locationId` (required) **Query:** `limit`, `after`, `before`

**Returns:** `{ items: [...], paging: { ... } }`

**PlayerPathOfLegendRanking shape:**

```json
{
  "tag": "#99GU92P0",
  "name": "TT-shadow.cr29",
  "expLevel": 78,
  "eloRating": 2247,
  "rank": 1,
  "clan": { "tag": "#R99R8G8J", "name": "Skyline", "badgeId": 16000134 }
}
```

| Field       | Type    | Notes                                                                                                 |
| ----------- | ------- | ----------------------------------------------------------------------------------------------------- |
| `tag`       | string  | Player tag                                                                                            |
| `name`      | string  |                                                                                                       |
| `expLevel`  | integer | Legacy experience level — retired in-game in 2026 (see [players.md](players.md)); treat as unreliable |
| `eloRating` | integer | Path of Legend ELO rating                                                                             |
| `rank`      | integer |                                                                                                       |
| `clan`      | object  | Optional — absent if not in a clan                                                                    |

**The board is capped at 1,000 places by the API, and the cap is a cut, not a floor.** Observed 2026-09-20 on
`/locations/global/pathoflegend/players`: `limit=5` returns 5 items and `paging.cursors.after`; `limit=1000` returns
exactly 1,000 items and `paging: { cursors: {} }` (no `after`); `limit=2000` also returns 1,000 with no cursor; and a
cursor placed at position 1000 (`after=eyJwb3MiOjEwMDB9`, `{"pos":1000}`) returns `items: []` with only a `before`
cursor. The list stops mid-tie: the last eight places all carried 2153–2155 that day, and on 2026-09-19 ranks 995–1000
all read 2111. So while fewer than 1,000 players are rated (the first days of a season, or a small country — Iceland
returned 2 items on 2026-09-20) the endpoint is everyone above the rating floor; once 1,000 are, the last place's
`eloRating` is a rank cutoff that rises through the season as the field plays (global: 1404 on 2026-09-10 when the board
first filled, 2111 on 2026-09-19), and a player whose rating did not move can drop hundreds of places or off the board.
Country boards cap the same way (United States and Japan both returned 1,000 with no cursor, tails at 1791 and 1737), so
a country's full board reaches far below the global cutoff. The population above the true floor is not observable from
this endpoint; a per-location sweep is a lower bound only.

Many locations have no board at all. Of 255 location boards read daily 2026-09-05 to 2026-09-25, 87 returned `items: []`
on every read, so an empty country board is normal, not a failed fetch.

**`eloRating` is the player's `currentPathOfLegendSeasonResult.trophies`, and the board `rank` is its `rank`.** Observed
2026-09-18 on the global board's #1 and #3: board `eloRating` 2711 / `rank` 1 against the same player's profile
`currentPathOfLegendSeasonResult { leagueNumber: 7, trophies: 2711, rank: 1 }`, and 2694 / 3 against
`{ leagueNumber: 7, trophies: 2694, rank: 3 }`, read within a minute of each other. The two endpoints name one number
two ways; a recorder can join a profile's Path of Legends standing to the board without a conversion. (The profile's
`trophies` is Trophy Road and unrelated: 10,714 and 14,000 for the same two players.)

---

## Global Tournament Rankings

### GET /locations/global/rankings/tournaments/{tournamentTag}

Get global player rankings for a specific tournament.

**Path:** `tournamentTag` (required, URL-encoded) **Query:** `limit`, `after`, `before`

**Returns:** `LadderTournamentRankingList`

Status note:

- Endpoint is documented and appears active
- Success shape was not re-verified in the March 2026 pass because `/globaltournaments` returned no active tournaments
- For agentic use, treat this endpoint as requiring fresh live validation before depending on exact field-level schema

---

## League Seasons (Global)

### GET /locations/global/seasons

List all historical league seasons.

**Query:** None

**Returns:** `{ items: [...], paging: { cursors: {} } }`

Items are `{ id: "YYYY-MM" }` objects. Note: early seasons (2016-2017) have duplicate entries for the same month. Season
IDs go from `2016-02` through the most recent completed season.

---

### GET /locations/global/seasonsV2

List league seasons with extended detail.

**Query:** None

**Returns:** `{ items: [...], paging: { cursors: {} } }`

**Current status:** Returns 137 items with all null fields (`{ code: null, uniqueId: null, endTime: null }`). This
endpoint is broken as of March 2026 — returns the correct count of seasons but with no data. Use `/seasons` (V1)
instead.

---

### GET /locations/global/seasons/{seasonId}

Get a single league season by ID.

**Path:** `seasonId` (required) — format `YYYY-MM`

**Returns:** `LeagueSeason` — `{ id: "YYYY-MM" }`

---

### GET /locations/global/seasons/{seasonId}/rankings/players

Get top trophy player rankings for a completed league season.

**Path:** `seasonId` (required) **Query:** `limit`, `after`, `before`

**Returns:** `PlayerRankingList`

**Current status:** Returns `{"reason":"notFound"}` for all tested seasons (2024 through 2026). In the March 2026 pass
the body contained only `reason` (no `message`). This endpoint appears to be permanently broken. Use Path of Legend
season rankings instead.

---

### GET /locations/global/pathoflegend/{seasonId}/rankings/players

Get top Path of Legend player rankings for a specific season.

**Path:** `seasonId` (required) — format `YYYY-MM` **Query:** `limit`, `after`, `before`

**Returns:** `{ items: [...], paging: { ... } }` — same shape as location PoL rankings

**Example:** `/locations/global/pathoflegend/2025-01/rankings/players?limit=2` returns:

```json
{
  "items": [
    { "tag": "#G9YV9GR8R", "name": "Mohamed Light", "expLevel": 70, "eloRating": 3874, "rank": 1, "clan": { ... } },
    { "tag": "#U8RYGC8GU", "name": "Polaris✨DEE", "expLevel": 57, "eloRating": 3844, "rank": 2, "clan": { ... } }
  ]
}
```

Observed 2026-09-11, probing with **numeric season ids**: the endpoint accepts them, and returns the season's FINAL
standings to a depth of `9999` items, no paging cursor. That depth is a cut, not the field: the `2026-08` board read on
2026-09-20 ends with ranks 9991–9999 all at `eloRating` 2342, so more players finished at that rating than the board
shows. **A numeric id is the 1-based position in the `/locations/global/seasons` list, NOT the clan-war `seasonId`**
from river races, and not the in-game "Season N" shown on the Pass — three different numbering namespaces that happen to
share monthly boundaries. Verified by matching `#1` players across the two forms: `136` = `2026-01`, `135` = `2025-12`
(`eloRating` 3914, `#9999` at 2222), `97` = `2022-10`. The clan-war season running on the probe date was also numbered
136, which made the numeric form look like the clan-war id; it is a coincidence. The V1 list carries duplicate early
entries, so derive the month from the list position, never from date arithmetic on the number — or just use the
`YYYY-MM` form, which is unambiguous. `87` (the in-game season number for September 2026) returns `notFound`. That is a
different view from the current-season `/locations/{id}/pathoflegend/players`, which lists only players above a rating
floor (869 rated on day 4 of the September 2026 season, the last at 1212) and whose ratings are still climbing.
**`2022-10` (position 97) is the earliest season with a board**; earlier positions return `items: []` — Path of Legend's
launch month. Forty-seven final boards (`2022-10` through `2026-08`) were being served on the probe date; nothing says
how long they will be.

### Season namespaces: what is canonical and what is derived

Observed 2026-09-17 (probing `/locations/global/seasons`, `/players/{tag}`, `/clans/{tag}/riverracelog`,
`/leaderboards`, and the PoL finals by both id forms). The API names a season by the **month it starts in, `YYYY-MM`**,
and every other season number is a derived label for the same monthly season:

| Where the key appears                                                                                      | Form                                            | Example (September 2026)                                                                                                                                                     |
| ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/locations/global/seasons` items, `leagueStatistics.previousSeason.id` / `bestSeason.id`, PoL finals path | `YYYY-MM`                                       | `2026-09` (absent from the list until it completes; `2026-08` was the last item on 2026-09-17)                                                                               |
| `Player.progress` keys and their arena `rawName`                                                           | `YYYYMM` inside a mode key                      | `seasonal-trophy-road-202609`, `2v2League_202609`, `SeasonalArenas_202609_Arena1`, `2v2League_202609Arena1`                                                                  |
| Badge names                                                                                                | `YYYYMM`                                        | `SeasonalBadge_202509`, `MergeTacticsBadge_202506`                                                                                                                           |
| River race log `seasonId`                                                                                  | integer                                         | `136` (week created `20260914T093805.000Z`); `135` for the week closed `20260907T093404.000Z`                                                                                |
| PoL finals numeric path id                                                                                 | 1-based position in the seasons list            | `143` = `2026-08`; `144` is `notFound` while the season runs                                                                                                                 |
| Merge Tactics                                                                                              | its own per-year counter                        | `AutoChess_2026_Season_11` (eleven seasons by September, so not monthly)                                                                                                     |
| Game-mode leaderboards (`/leaderboards`)                                                                   | one numeric board id per run                    | 2v2 League has appeared as `170000003`, `170000004`, `170000007`, `170000014`, `743144`                                                                                      |
| In-game Pass season                                                                                        | not in the API, neither the number nor the name | "Season 87", "Minion Academy" (September 2026); `/events`, `/players`, `/clans/{tag}/currentriverrace`, `/globaltournaments` and the seasons list carry neither (2026-09-17) |

**The seasons list is one entry per season, not per month.** Its 143 items on 2026-09-17 cover 127 months
(`2016-02`..`2026-08`) because fourteen months in `2016-02`..`2017-03` carry two entries and `2016-05` and `2016-10`
carry three: seasons were shorter then. From `2017-04` on, one entry per month.

**The river-race `seasonId` is the seasons-list position minus 8**, checked at six points against a recorder's
`riverracelog` history: `2025-03` (position 126) = `118`, `2025-04` = `119`, `2025-05` = `120`, `2026-02` = `129`,
`2026-08` (143) = `135`, `2026-09` (would be 144) = `136`. What the eight early positions are is not recoverable from
the API; the relation has held for every monthly season since `2017-04`. A live `currentriverrace` never carries the id,
so the only way to learn the current war season number from the API is the previous week's log entry plus one at the
month boundary, or this derivation from the month.

**Path of Legends carries no season id anywhere on the player** (`currentPathOfLegendSeasonResult` and friends are
`{ leagueNumber, trophies, rank }`); the season is the current month, and its settled standing is the finals board
addressed by `YYYY-MM`.

For a recorder: key seasons by `YYYY-MM`, derive the war integer from the list position (and verify it against the next
`riverracelog` entry), take mode keys such as `AutoChess_2026_Season_11` verbatim from `progress` as their own
identifiers, and do not try to name the Pass season: neither its number nor its name ("Minion Academy") is exposed
anywhere, so a recorder cannot derive it.

---

## Error Codes

| Code | Meaning                                 |
| ---- | --------------------------------------- |
| 400  | Bad parameters                          |
| 403  | Auth failure / insufficient token scope |
| 404  | Resource not found                      |
| 429  | Rate limit exceeded                     |
| 500  | Server error                            |
| 503  | Maintenance                             |

Observed error bodies are usually `{ reason, message? }`. Invalid `locationId` values return `400 badRequest` with a
message such as `Unknown value for parameter locationId`. `type`/`detail` were not observed.

---

## Agent Notes

- `locationId` for global endpoints is the literal string `global` — e.g. `/locations/global/seasons`
- `/seasonsV2` is broken (all null fields) — use `/seasons` (V1) to get season IDs. Still broken 2026-09-11: 143 items,
  every field null.
- `seasonId` format is `YYYY-MM` (e.g. `2025-01`). Seasons go back to `2016-02`. Early seasons (2016-2017) have
  duplicate entries.
- Trophy rankings (`/rankings/players`) and Path of Legend rankings (`/pathoflegend/players`) are separate leaderboards
  for the same location
- `/rankings/clanwars` reflects river race performance, not classic war
- To get a `locationId` for a known country, fetch `/locations` and match by `countryCode` or `name`
- **Season trophy rankings are broken** — `/seasons/{id}/rankings/players` returns notFound for all seasons. Use PoL
  season rankings.
- `previousRank` of `-1` in clan rankings means the clan was not previously ranked
- **Player trophy rankings** (`/rankings/players`) have returned empty both early in a season (2026-09-10, `global` and
  United States) and in a season's last week (2026-09-05, one archived read); treat the board as unavailable, as above.
  PoL global rankings and clan rankings work consistently.
- `/locations` returns all 262 locations with no limit by default. No pagination needed for the full list.
- `/locations?limit=0` returns `400 badRequest`
- Cache duration: location data is cached ~10 minutes server-side; rankings ~1 minute
