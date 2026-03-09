# Clash Royale API – Cards Endpoints

Base URL: `https://api.clashroyale.com/v1`
Auth: Bearer token in `Authorization` header

---

## Endpoints

### GET /cards
Get the full list of available cards in the game.

**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `Items` object with fields:
- `items` (ItemList) — standard cards (troops, spells, buildings)
- `supportItems` (ItemList) — Tower Troops (Tower Princess, Cannoneer, etc.)

**Card fields (per item):**
- `name` (string), `id` (integer)
- `maxLevel` (integer), `maxEvolutionLevel` (integer, optional — only on cards with evolutions)
- `elixirCost` (integer — not present on supportItems)
- `rarity` (string) — `common`, `rare`, `epic`, `legendary`, `champion`
- `iconUrls` (object) — `medium` (always present), `heroMedium` (optional), `evolutionMedium` (optional)

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
- This is a global catalog endpoint — not player-specific; use `/players/{playerTag}` for a player's collected cards with levels
- `items` vs `supportItems`: Tower Troops (cards that replace/augment crown towers) are in `supportItems`; everything else is in `items`
- Pagination available but the full card list is small enough that a single unpaginated call typically returns everything


