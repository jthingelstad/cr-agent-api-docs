# Clash Royale API – Locations Endpoints

Base URL: `https://api.clashroyale.com/v1`
Auth: Bearer token in `Authorization` header
Tag encoding: `#2ABC` → `%232ABC` in path

---

## Endpoints

### GET /locations
List all available locations (countries + global).

**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `LocationList` — array of `Location` objects

---

### GET /locations/{locationId}
Get a single location by ID.

**Path:** `locationId` (required)

**Returns:** `Location` object with fields:
- `id`, `name`, `localizedName`, `countryCode`, `isCountry`

---

## Location Rankings

### GET /locations/{locationId}/rankings/players
Get trophy leaderboard for players in a location.

**Path:** `locationId` (required)
**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `PlayerRankingList` — array of `PlayerRanking`

---

### GET /locations/{locationId}/rankings/clans
Get trophy leaderboard for clans in a location.

**Path:** `locationId` (required)
**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `ClanRankingList` — array of `ClanRanking`

---

### GET /locations/{locationId}/rankings/clanwars
Get clan war leaderboard for a location.

**Path:** `locationId` (required)
**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `ClanRankingList` — array of `ClanRanking`

---

### GET /locations/{locationId}/pathoflegend/players
Get Path of Legend player rankings for a location (current season).

**Path:** `locationId` (required)
**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `PlayerPathOfLegendRankingList` — array of `PlayerPathOfLegendRanking`

---

## Global Tournament Rankings

### GET /locations/global/rankings/tournaments/{tournamentTag}
Get global player rankings for a specific tournament.

**Path:** `tournamentTag` (required)
**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `LadderTournamentRankingList` — array of `LadderTournamentRanking`

---

## League Seasons (Global)

### GET /locations/global/seasons
List all historical top player league seasons.

**No parameters**

**Returns:** `LeagueSeasonList` — array of `LeagueSeason` (id only)

---

### GET /locations/global/seasonsV2
List league seasons with extended detail (unique IDs + end times). Prefer over `/seasons`.

**No parameters**

**Returns:** `LeagueSeasonList` — array of `LeagueSeason` with additional fields

---

### GET /locations/global/seasons/{seasonId}
Get a single league season by ID.

**Path:** `seasonId` (required)

**Returns:** `LeagueSeason` — `{ id }`

---

### GET /locations/global/seasons/{seasonId}/rankings/players
Get top trophy player rankings for a completed league season.

**Path:** `seasonId` (required)
**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `PlayerRankingList` — array of `PlayerRanking`

---

### GET /locations/global/pathoflegend/{seasonId}/rankings/players
Get top Path of Legend player rankings for a specific season.

**Path:** `seasonId` (required)
**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `PlayerPathOfLegendRankingList` — array of `PlayerPathOfLegendRanking`

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad parameters |
| 403 | Auth failure / insufficient token scope |
| 404 | Location/season not found |
| 429 | Rate limit exceeded |
| 500 | Server error |
| 503 | Maintenance |

All errors return: `{ reason, message, type, detail }`

---

## Agent Notes
- `locationId` for global endpoints is the literal string `global` — e.g. `/locations/global/seasons`
- Use `/seasonsV2` over `/seasons` — it includes season end times needed for temporal context
- `seasonId` format is typically `YYYY-MM` (e.g. `2024-03`) — verify via `/seasonsV2` before constructing
- Trophy rankings (`/rankings/players`) and Path of Legend rankings (`/pathoflegend/players`) are separate leaderboards for the same location
- `/rankings/clanwars` reflects river race performance, not classic war
- To get a `locationId` for a known country, fetch `/locations` and match by `countryCode` or `name`

