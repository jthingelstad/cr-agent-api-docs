# Clash Royale API – Players Endpoints

Base URL: `https://api.clashroyale.com/v1`
Auth: Bearer token in `Authorization` header
Tag encoding: `#2ABC` → `%232ABC` in path

---

## Endpoints

### GET /players/{playerTag}
Get full player profile.

**Path:** `playerTag` (required) — URL-encoded player tag

**Returns:** `Player` object with fields:
- `tag`, `name`, `expLevel`, `expPoints`, `totalExpPoints`, `starPoints`
- `trophies`, `bestTrophies`, `arena`, `role`
- `wins`, `losses`, `battleCount`, `threeCrownWins`
- `donations`, `donationsReceived`, `totalDonations`
- `challengeCardsWon`, `challengeMaxWins`
- `tournamentCardsWon`, `tournamentBattleCount`
- `warDayWins`, `clanCardsCollected`
- `clan` (PlayerClan), `leagueStatistics`
- `currentDeck`, `currentDeckSupportCards` (PlayerItemLevelList)
- `cards`, `supportCards` (full collection with levels)
- `currentFavouriteCard` (Item)
- `badges`, `achievements`
- `currentPathOfLegendSeasonResult`, `lastPathOfLegendSeasonResult`, `bestPathOfLegendSeasonResult`
- `legacyTrophyRoadHighScore`, `progress`

---

### GET /players/{playerTag}/battlelog
Get recent battle history.

**Path:** `playerTag` (required)

**Returns:** `BattleList` — array of `Battle` objects

---

### GET /players/{playerTag}/upcomingchests
Get the player's upcoming chest sequence.

**Path:** `playerTag` (required)

**Returns:** `UpcomingChests` with `items` (ChestList array)

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad parameters |
| 403 | Auth failure / insufficient token scope |
| 404 | Player not found |
| 429 | Rate limit exceeded |
| 500 | Server error |
| 503 | Maintenance |

All errors return: `{ reason, message, type, detail }`

---

## Agent Notes
- `currentDeck` vs `cards`: `currentDeck` is the active 8-card deck; `cards` is the full collection with level data
- `role` enum covers: member, elder, coLeader, leader (+ possibly none/unaffiliated)
- Path of Legend fields will be null outside of season or for players below Legend League
- `battlelog` is recent only — no pagination, no date filter
- `upcomingchests` reflects the next N chests in the rotation cycle


