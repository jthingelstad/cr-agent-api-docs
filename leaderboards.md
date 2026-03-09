# Clash Royale API – Leaderboards Endpoints

Base URL: `https://api.clashroyale.com/v1`
Auth: Bearer token in `Authorization` header

---

## Endpoints

### GET /leaderboards
List all available leaderboards (different trophy roads).

**No parameters**

**Returns:** `LeaderboardList` — array of `Leaderboard` objects containing leaderboard metadata including IDs

---

### GET /leaderboard/{leaderboardId}
Get players ranked on a specific leaderboard.

**Path:** `leaderboardId` (required, integer) — obtain from `GET /leaderboards`
**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `LeaderboardList` — array of `Leaderboard` objects with player ranking entries

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad parameters |
| 403 | Auth failure / insufficient token scope |
| 404 | Leaderboard not found |
| 429 | Rate limit exceeded |
| 500 | Server error |
| 503 | Maintenance |

All errors return: `{ reason, message, type, detail }`

---

## Agent Notes
- Two-step pattern: fetch `/leaderboards` first to get valid `leaderboardId` values, then fetch `/leaderboard/{id}` for players
- `leaderboardId` is an integer (unlike most CR API identifiers which are string tags)
- Distinct from `/locations/{locationId}/rankings` — these leaderboards are trophy-road specific rather than geography-specific
- `/leaderboards` (plural) lists metadata; `/leaderboard/{id}` (singular) returns players — note the inconsistent singular/plural naming


