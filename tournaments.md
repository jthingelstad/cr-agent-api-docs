# Clash Royale API – Tournaments Endpoints

Base URL: `https://api.clashroyale.com/v1`
Auth: Bearer token in `Authorization` header
Tag encoding: `#2ABC` → `%232ABC` in path

---

## Endpoints

### GET /tournaments
Search tournaments by name.

**Query:**
- `name` — wildcard match, 3+ chars required
- `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `TournamentHeaderList` — array of `TournamentHeader` objects (summary data, not full detail)

---

### GET /tournaments/{tournamentTag}
Get full tournament details.

**Path:** `tournamentTag` (required) — URL-encoded tournament tag

**Returns:** `Tournament` object with fields:
- `tag`, `name`, `description`, `type` (enum, 3 values)
- `status` (enum, 4 values)
- `creatorTag`
- `capacity`, `maxCapacity`, `levelCap`
- `duration`, `preparationDuration`
- `createdTime`, `startedTime`, `endedTime`
- `firstPlaceCardPrize`
- `gameMode` (GameMode object)
- `membersList` (TournamentMemberList)

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad parameters |
| 403 | Auth failure / insufficient token scope |
| 404 | Tournament not found |
| 429 | Rate limit exceeded |
| 500 | Server error |
| 503 | Maintenance |

All errors return: `{ reason, message, type, detail }`

---

## Agent Notes
- Search returns `TournamentHeader` (summary) — fetch by tag to get `membersList` and full detail
- `status` enum likely covers: inPreparation, inProgress, ended, cancelled
- `type` enum likely covers: open, passwordProtected, private
- No ordering guarantee on search results
- `levelCap` sets the max card level allowed — relevant context for tournament commentary


