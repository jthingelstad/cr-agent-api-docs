# Clash Royale API – Clans Endpoints

Base URL: `https://api.clashroyale.com/v1`
Auth: Bearer token in `Authorization` header
Tag encoding: `#2ABC` → `%232ABC` in path

---

## Endpoints

### GET /clans/{clanTag}
Get full clan info including member list, scores, description, badge.

**Path:** `clanTag` (required) — URL-encoded clan tag

**Returns:** `Clan` object with fields:
- `tag`, `name`, `description`, `type` (open/inviteOnly/closed)
- `members` (count), `memberList` (array)
- `clanScore`, `clanWarTrophies`, `requiredTrophies`
- `donationsPerWeek`, `badgeId`, `badgeUrls`, `location`

---

### GET /clans/{clanTag}/members
List clan members (paginated).

**Path:** `clanTag` (required)
**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `ClanMemberList` array of `ClanMember` objects

---

### GET /clans/{clanTag}/currentriverrace
Get the clan's active river race state.

**Path:** `clanTag` (required)

**Returns:** `CurrentRiverRace` with fields:
- `state` (enum), `sectionIndex`, `periodIndex`, `periodType`
- `clan` (RiverRaceClan), `clans` (all clans in race)
- `collectionEndTime`, `warEndTime`
- `periodLogs` (PeriodLogList)

---

### GET /clans/{clanTag}/riverracelog
Historical river race results (paginated).

**Path:** `clanTag` (required)
**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `RiverRaceLog` array of `RiverRaceLogEntry`

---

### GET /clans/{clanTag}/currentwar
Get current classic clan war status.

**Path:** `clanTag` (required)

**Returns:** `CurrentClanWar` with fields:
- `state` (enum, 7 values), `clan`, `participants`, `clans`
- `collectionEndTime`, `warEndTime`

---

### GET /clans/{clanTag}/warlog
Historical classic clan war log (paginated).

**Path:** `clanTag` (required)
**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `ClanWarLog` array of `ClanWarLogEntry`

---

### GET /clans
Search clans by name/criteria. At least one filter required. Name must be 3+ chars.

**Query:**
- `name` — wildcard match anywhere in name
- `locationId`, `minMembers`, `maxMembers`, `minScore`
- `limit`, `after`, `before`

**Returns:** `ClanList` array of `Clan` objects

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad parameters |
| 403 | Auth failure / insufficient token scope |
| 404 | Clan not found |
| 429 | Rate limit exceeded |
| 500 | Server error |
| 503 | Maintenance |

All errors return: `{ reason, message, type, detail }`

---

## Agent Notes
- Pagination: use `paging.cursors` from response to get `after`/`before` values
- `currentriverrace` vs `currentwar`: river race is the current war format; `currentwar` is legacy
- For POAP KINGS clan tag: `#XXXXXXXXX` → path param `%23XXXXXXXXX`

