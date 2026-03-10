# Clash Royale API – Cards Endpoints

Base URL: `https://api.clashroyale.com/v1`
Auth: Bearer token in `Authorization` header

---

## Endpoints

### GET /cards
Get the full list of available cards in the game.

**Query:** `limit`, `after`, `before` (pagination cursors — mutually exclusive)

**Returns:** `Items` object with two arrays:
- `items` — 121 standard cards (troops, spells, buildings)
- `supportItems` — 4 Tower Troops

**Standard card shape (`items`):**
```json
{
  "name": "Knight",
  "id": 26000000,
  "maxLevel": 16,
  "maxEvolutionLevel": 3,
  "elixirCost": 3,
  "iconUrls": {
    "medium": "https://api-assets.clashroyale.com/cards/300/...",
    "heroMedium": "https://api-assets.clashroyale.com/cardheroes/300/...",
    "evolutionMedium": "https://api-assets.clashroyale.com/cardevolutions/300/..."
  },
  "rarity": "common"
}
```

**Support card shape (`supportItems`):**
```json
{
  "name": "Tower Princess",
  "id": 159000000,
  "maxLevel": 16,
  "iconUrls": { "medium": "https://api-assets.clashroyale.com/cards/300/..." },
  "rarity": "common"
}
```
Support items lack `elixirCost` and `maxEvolutionLevel`.

**Rarity → maxLevel mapping (observed):**

| Rarity | maxLevel |
|--------|----------|
| common | 16 |
| rare | 14 |
| epic | 11 |
| legendary | 8 |
| champion | 6 |

**iconUrls variants:**
- `medium` — always present on all cards
- `heroMedium` — present on some cards (hero/star skins)
- `evolutionMedium` — present only on cards with evolutions (46 of 121 cards)

**ID ranges (observed):**
- `26000xxx` — troops
- `27000xxx` — buildings
- `28000xxx` — spells
- `159000xxx` — Tower Troops (supportItems)

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
- Global catalog endpoint — not player-specific. Use `/players/{playerTag}` for a player's collected cards with levels.
- `items` vs `supportItems`: Tower Troops (cards that replace/augment crown towers) are in `supportItems`; everything else is in `items`
- Pagination available but the full list (121 + 4 = 125 cards) is small enough that a single unpaginated call returns everything
- `maxEvolutionLevel` is optional — only 46/121 standard cards have evolutions (values observed: 1, 2, or 3)
- No `paging` object in response when all cards fit in one page (cursors will be empty)
