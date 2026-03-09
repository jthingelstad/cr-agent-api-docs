# Clash Royale API – Global Tournaments Endpoints

Base URL: `https://api.clashroyale.com/v1`
Auth: Bearer token in `Authorization` header

---

## Endpoints

### GET /globaltournaments
Get list of global tournaments.

**No parameters**

**Returns:** `LadderTournamentList` — array of `LadderTournament` objects

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad parameters |
| 403 | Auth failure / insufficient token scope |
| 404 | Not found |
| 429 | Rate limit exceeded |
| 500 | Server error |
| 503 | Maintenance |

All errors return: `{ reason, message, type, detail }`

---

## Agent Notes
- Single endpoint, no parameters — fetch and parse
- Returns `LadderTournament` type — distinct from the player-created `Tournament` type returned by `/tournaments/{tag}`
- To get player rankings for a global tournament, use `tournamentTag` from results with `/locations/global/rankings/tournaments/{tournamentTag}` (see Locations reference)


