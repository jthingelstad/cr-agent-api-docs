# Clash Royale API — Reference Index

This is a reference documentation set for the Clash Royale API (`https://api.clashroyale.com/v1`). Each file covers a domain of endpoints, their parameters, response types, and implementation notes.

---

## Common Patterns

### Authentication

All endpoints require a Bearer token in the `Authorization` header. Tokens are created at [developer.clashroyale.com](https://developer.clashroyale.com) and are IP-restricted.

### Tag Encoding

Player, clan, and tournament tags start with `#` which must be URL-encoded as `%23` in path parameters:

`#2ABC` → `%232ABC`

This applies to all endpoints that accept a tag in the path (`playerTag`, `clanTag`, `tournamentTag`).

### Pagination

Endpoints that return lists support cursor-based pagination:

- `limit` — maximum number of items to return
- `after` — cursor for next page (from `paging.cursors.after` in response)
- `before` — cursor for previous page (from `paging.cursors.before` in response)

`after` and `before` are mutually exclusive. Omit both for the first page.

### Error Responses

All endpoints return the same error format:

| Code | Meaning |
|------|---------|
| 400 | Bad parameters |
| 403 | Auth failure / insufficient token scope |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Server error |
| 503 | Maintenance |

Error body: `{ reason, message, type, detail }`

---

## Endpoint Reference

### Players — [players.md](players.md)
Player profiles, battle logs, and upcoming chests.

| Endpoint | Description |
|----------|-------------|
| `GET /players/{playerTag}` | Full player profile |
| `GET /players/{playerTag}/battlelog` | Recent battle history |
| `GET /players/{playerTag}/upcomingchests` | Upcoming chest sequence |

### Clans — [clans.md](clans.md)
Clan info, members, river race, classic war, and search.

| Endpoint | Description |
|----------|-------------|
| `GET /clans/{clanTag}` | Full clan info |
| `GET /clans/{clanTag}/members` | Clan member list (paginated) |
| `GET /clans/{clanTag}/currentriverrace` | Active river race state |
| `GET /clans/{clanTag}/riverracelog` | Historical river race results |
| `GET /clans/{clanTag}/currentwar` | Classic clan war status (legacy) |
| `GET /clans/{clanTag}/warlog` | Classic war log (legacy) |
| `GET /clans` | Search clans by name/criteria |

### Tournaments — [tournaments.md](tournaments.md)
Player-created tournaments.

| Endpoint | Description |
|----------|-------------|
| `GET /tournaments` | Search tournaments by name |
| `GET /tournaments/{tournamentTag}` | Full tournament details |

### Global Tournaments — [globaltournaments.md](globaltournaments.md)
Supercell-run global tournaments.

| Endpoint | Description |
|----------|-------------|
| `GET /globaltournaments` | List active global tournaments |

### Locations & Rankings — [locations.md](locations.md)
Location lookups, regional rankings, global tournament rankings, and league seasons.

| Endpoint | Description |
|----------|-------------|
| `GET /locations` | List all locations |
| `GET /locations/{locationId}` | Single location by ID |
| `GET /locations/{locationId}/rankings/players` | Player trophy rankings by location |
| `GET /locations/{locationId}/rankings/clans` | Clan trophy rankings by location |
| `GET /locations/{locationId}/rankings/clanwars` | Clan war rankings by location |
| `GET /locations/{locationId}/pathoflegend/players` | Path of Legend player rankings by location |
| `GET /locations/global/rankings/tournaments/{tournamentTag}` | Global tournament player rankings |
| `GET /locations/global/seasons` | List league seasons |
| `GET /locations/global/seasonsV2` | List league seasons (preferred, includes end times) |
| `GET /locations/global/seasons/{seasonId}` | Single league season |
| `GET /locations/global/seasons/{seasonId}/rankings/players` | Season trophy rankings |
| `GET /locations/global/pathoflegend/{seasonId}/rankings/players` | Season Path of Legend rankings |

### Leaderboards — [leaderboards.md](leaderboards.md)
Trophy-road-specific leaderboards (distinct from location rankings).

| Endpoint | Description |
|----------|-------------|
| `GET /leaderboards` | List available leaderboards |
| `GET /leaderboard/{leaderboardId}` | Player rankings for a leaderboard |

### Cards — [cards.md](cards.md)
Game card catalog.

| Endpoint | Description |
|----------|-------------|
| `GET /cards` | Full card list (standard + Tower Troops) |

### Challenges — [challenges.md](challenges.md)
Active and upcoming in-game challenges.

| Endpoint | Description |
|----------|-------------|
| `GET /challenges` | Current and upcoming challenges |

### Events — [events.md](events.md)
Current in-game events.

| Endpoint | Description |
|----------|-------------|
| `GET /events` | All active events |

---

## Supporting Reference

### Data Models — [models.md](models.md)
Complete reference of all API response types, their fields, and which endpoints use them. Read this to understand response shapes and model nesting.

### Fan Content Policy — [fan-content-policy.md](fan-content-policy.md)
Supercell's rules for using their assets in fan-created content. Includes required disclaimer text, permitted/prohibited activities, and monetization guidelines.

---

## Cross-Reference Notes

- **Global tournaments → location rankings:** Use `tournamentTag` from `/globaltournaments` with `/locations/global/rankings/tournaments/{tournamentTag}` to get player rankings
- **River race vs classic war:** `/currentriverrace` is the current format; `/currentwar` is legacy. Both are under `/clans/{clanTag}/`
- **Trophy rankings vs Path of Legend:** These are separate leaderboards at the same location — `/rankings/players` for trophies, `/pathoflegend/players` for Path of Legend
- **Leaderboards vs location rankings:** `/leaderboards` are trophy-road-specific; `/locations/{id}/rankings` are geography-specific
- **Tournaments vs global tournaments:** `/tournaments` covers player-created tournaments; `/globaltournaments` covers Supercell-run events. Different model types (`Tournament` vs `LadderTournament`)
- **Season format:** League season IDs use `YYYY-MM` format (e.g. `2024-03`) — verify via `/seasonsV2` before constructing
