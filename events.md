# Clash Royale API – Events Endpoints

Base URL: `https://api.clashroyale.com/v1`
Auth: Bearer token in `Authorization` header

---

## Endpoints

### GET /events
Get all current in-game events.

**No parameters**

**Returns:** bare JSON array of `TrailEvent` objects (not wrapped in `{ items: [...] }`)

**TrailEvent fields:**
- `eventTag` (string) — e.g. `#R8U2RCJ`
- `title` (string) — localized event name
- `description` (string, nullable) — localized event description

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
- `title` and `description` are localized — locale is determined by the API token's configured region
- `description` can be null for some events
- Returns only currently active events, not upcoming or historical
- Useful for Elixir clan commentary context (e.g. referencing an active event in posts)


