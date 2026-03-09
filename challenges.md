# Clash Royale API – Challenges Endpoints

Base URL: `https://api.clashroyale.com/v1`
Auth: Bearer token in `Authorization` header

---

## Endpoints

### GET /challenges
Get all current and upcoming challenges.

**No parameters**

**Returns:** `ChallengeChainsList` — array of `ChallengeChain` objects

**Chain structure:**
- Each chain is of type `singleChallenge` or `challengeChain`
- Prize types: `none`, `cardStack`, `chest`, `cardStackRandom`, `resource`, `tradeToken`, `consumable`

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
- Single endpoint, no parameters — just fetch and parse
- `singleChallenge` is a standalone challenge; `challengeChain` is a sequence of challenges that must be completed in order
- Returns both active and upcoming challenges — check timing fields to determine current state
- Prize type `cardStackRandom` indicates a random card reward; useful context for player-facing commentary


