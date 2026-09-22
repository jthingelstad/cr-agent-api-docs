# Battle Models

Battle-log field shapes verified against live API responses (March-April 2026).

## Battle

Used by `GET /players/{playerTag}/battlelog`, which returns a bare JSON array.

```json
{
  "type": "PvP",
  "battleTime": "20260309T025623.000Z",
  "isLadderTournament": false,
  "arena": { "id": 54000141, "name": "Magic Academy", "rawName": "Arena_L15" },
  "gameMode": { "id": 72000006, "name": "Ladder" },
  "deckSelection": "collection",
  "team": [],
  "opponent": [],
  "isHostedMatch": false,
  "leagueNumber": 1
}
```

Verified fields:

- `type`
- `battleTime`
- `isLadderTournament`
- `tournamentTag?`
- `eventTag?`
- `arena`
- `gameMode`
- `deckSelection`
- `team`
- `opponent`
- `modifiers?`
- `isHostedMatch`
- `leagueNumber`
- `boatBattleSide?`
- `boatBattleWon?`
- `newTowersDestroyed?`
- `prevTowersDestroyed?`
- `remainingTowers?`

Official Swagger also lists `challengeWinCountBefore`, `challengeId`, and `challengeTitle` on `Battle`. They were not
observed in the March-April 2026 live-call pass; treat them as optional official-only fields until seen in payloads.

Observed battle types:

- `PvP`
- `pathOfLegend`
- `trail`
- `clanMate`
- `clanMate2v2`
- `friendly`
- `riverRacePvP`
- `riverRaceDuel`
- `riverRaceDuelColosseum`
- `tournament`
- `boatBattle`
- `unknown`

Observed deck selections:

- `collection`
- `eventDeck`
- `draft`
- `warDeckPick`
- `pick`
- `draftCompetitive`
- `predefined`
- `quadDeckPick`

## Battle Length And Phases

**The battle log carries no duration.** There is no `duration`, no start/end pair and no elapsed field on `Battle`;
`battleTime` is a single instant, and whether it marks the battle's start or its finish is not established here. The
`duration` field that does exist in the API belongs to tournaments, not battles. What follows is the game's own clock,
which is what lets a reader bound a battle's length from the fields that ARE served.

A standard 1v1 runs a maximum of 5:00, in five one-minute segments (Supercell support documentation, recorded
2026-09-22):

| Battle clock         | Elapsed   | Phase        | Elixir |
| -------------------- | --------- | ------------ | ------ |
| 3:00 → 2:00          | 0:00-1:00 | Regulation   | 1x     |
| 2:00 → 1:00          | 1:00-2:00 | Regulation   | 1x     |
| 1:00 → 0:00          | 2:00-3:00 | Regulation   | 2x     |
| Overtime 2:00 → 1:00 | 3:00-4:00 | Sudden death | 2x     |
| Overtime 1:00 → 0:00 | 4:00-5:00 | Sudden death | 3x     |

The transitions are at **120 s** (double elixir), **180 s** (regulation ends) and **240 s** (triple elixir) elapsed. A
consumer modelling the timeline wants four phases - `REGULATION_SINGLE` → `REGULATION_DOUBLE` → `OVERTIME_DOUBLE` →
`OVERTIME_TRIPLE` - and special modes override all of it (see [game-modes.md](../game-modes.md): Double / Triple /
Infinite Elixir, Sudden Death, Ramp Up, and the rotating `Overtime_Ladder` label).

Two victory gates decide when the clock stops:

1. **Before 3:00**, destroying the opponent's King Tower ends the match immediately. This is the only way a battle ends
   early.
2. **At 3:00**, the side with more towers remaining wins. If they are level, a 2-minute sudden-death overtime begins and
   the next tower destroyed ends it. If no tower falls by 5:00, a tower-hitpoints tiebreaker resolves the match.

### What that lets you infer about a battle's length

Crowns are towers destroyed, so the crown pair bounds the duration:

| Observed                       | What it means                            | Duration         |
| ------------------------------ | ---------------------------------------- | ---------------- |
| Either side has 3 crowns       | A King Tower fell; the match ended then  | Unknown, ≤ 5:00  |
| Crowns unequal, neither side 3 | No King Tower fell, so regulation ran    | ≥ 3:00, ≤ 5:00   |
| Crowns EQUAL (level)           | Overtime expired without a tower falling | **Exactly 5:00** |

The level-crown row is the only case that pins a battle's length exactly, and it is rare: **125 of 229,390 recorded 1v1
battles (0.05%)**, measured across the whole corpus 2026-09-22. Every one of the 125 is a **draw** - not one was
resolved for a winner. That is the tiebreaker's own logic closing the loop: level crowns almost always means neither
side damaged a tower, so the tower hitpoints it compares are exactly equal and it cannot separate them either. Expect
the exactly-5:00 case to be a draw; a tiebreaker-decided battle is theoretically reachable (level crowns, unequal tower
hitpoints, a win/loss outcome) but did not occur once in this corpus.

Three-crown finishes were 17.3% of Path of Legends battles, 33.4% of ladder and 43.1% of river race, and inside Path of
Legends the rate falls monotonically with rating (19.0% at the 1000 band down to 10.5% at 3500). So the useful signal is
the FLOOR, not the exact case: 82.7% of ranked battles, 66.6% of ladder and 56.9% of war are provably three minutes or
longer, and better opponents push that share up.

**No crown is awarded for winning the tiebreaker.** Checked on 221 head-to-head rows with tower data (2026-09-22): the
crowns a side scored equalled the towers its opponent actually lost on every row, with no case of a crown without a
fallen tower.

### `elixirLeaked` bounds the duration from below

`elixirLeaked` is elixir generated while the bar was already full, so it cannot exceed what the match had time to
generate - which makes it a genuine lower bound on elapsed time, and the only per-battle one the payload carries. Two
level-crown battles read 166.18 / 173.18 and 168.29 / 179.54 with every tower untouched: both players idle for the whole
match, leaking nearly everything a full five minutes can produce. A `crowns 3-3` row from the same class read 0.0 /
0.82 - a match that never ran. The exact 1x generation rate is not verified in this repo, so treat the bound
qualitatively (a leak in the hundreds cannot come from a short battle) rather than inverting it to a number.

Do NOT read `elixirLeaked` as skill on an ordinary battle: holding elixir to make the opponent commit first raises it by
design, and the payload has no placement timestamps to separate that from waste.

Duel rows (`riverRaceDuel`, `riverRaceDuelColosseum`) sum crowns across up to three games, so none of the above applies
to them; `boatBattle` is an attack on a static defense with no overtime. Restrict any duration inference to head-to-head
types.

## `trail` is the Seasonal Trophy Road, and its card levels are not the player's

`type: "trail"` is not a legacy value and not a party-mode bucket, though it collects those too. Since the **June 2026
update** it is overwhelmingly the reworked **Seasonal Trophy Road** - the Seasonal Road, with Seasonal Arena I (your own
deck) and Seasonal Arena II (your eight most-won-with cards banned, and low cards boosted to a minimum Level 15).

Observed in a 370k-battle record (2026-09-22), counting battles whose `gameMode.name` is `Ladder`:

| month   | `type: PvP` | `type: trail` | trail share |
| ------- | ----------- | ------------- | ----------- |
| 2026-03 | 4,377       | 0             | 0%          |
| 2026-05 | 4,909       | 0             | 0%          |
| 2026-06 | 4,678       | 323           | 6.5%        |
| 2026-07 | 5,322       | 555           | 9.4%        |
| 2026-08 | 5,269       | 1,049         | 16.6%       |
| 2026-09 | 5,458       | **11,651**    | **68.1%**   |

It appears in June 2026 and takes over. Two consequences for any consumer:

1. **It behaves like Trophy Road on trophies.** A `trail` Ladder loss deducts (12,993 of 13,578 losses carry a negative
   `trophyChange`, against 35,033 of 36,716 for `PvP`), and wins award. So trophy mechanics will NOT tell these apart,
   and a "seasonal trophies do not deduct" rule from an older limited-time Trail event does not hold here.
2. **The card levels are the format's, not the player's.** Mean recorded deck level is **15.87 on `trail` Ladder against
   13.67 on `PvP` Ladder**; the median is exactly **16.00**, and **99.9%** of `trail` decks sit at 14.5 or above against
   52.8% for `PvP`. That is Seasonal Arena II's Level 15 floor. Pooling the two populations for a card-level, level-gap
   or deck-strength comparison measures the arena, not the player.

So `gameMode.name` alone does not identify a population, and neither does `type`: the pair does. The same ruleset name
recurs under several types (24 of 62 observed modes do), because `gameMode` is the RULESET and `type` is the CONTEXT it
was played in - `Crazy_Arena` appears under `trail`, `friendly`, `unknown` and `clanMate`; `TeamVsTeam` under `trail`
and `clanMate2v2`; `CW_Duel_1v1` under both river-race duel types.

## Winner Inference

There is no explicit `winner` field. Use this order:

1. If `boatBattleWon` exists, use it.
2. Else if `team[0].trophyChange` exists and is non-zero **and the two sides moved in OPPOSITE directions**, positive
   means win and negative means loss. Zero means unresolved/draw.
3. Else if both sides have crowns, compare `team[0].crowns` and `opponent[0].crowns`.
4. Else treat the outcome as unresolved.

**Both sides can lose rating in the same battle.** Path of Legends penalises BOTH players for a draw, so a sign read per
side in isolation reports two losses - a result the game cannot produce. Observed in the raw payload 2026-09-22 for
`20260914T130806.000Z`:

```json
"team":     [{ "crowns": 3, "kingTowerHitPoints": 0, "trophyChange": -15 }],
"opponent": [{ "crowns": 3, "kingTowerHitPoints": 0, "trophyChange": -14 }]
```

Both sides at three crowns with both King Towers destroyed is not a battle state; the two changes summed to -29, as they
did on every instance of this shape. Check the OTHER side's sign before trusting your own, and fall through to the
crowns when they agree - the crowns say `draw`, which is correct. This shape was 0.020% of recorded Path of Legends
battles and never appeared in ladder or river race, which carry no such double penalty.

For 2v2 battles, use the first team entry because teammates share the same result.

## PlayerBattleData

```json
{
  "tag": "#PU9RCVYUG",
  "name": "FJ21",
  "crowns": 3,
  "kingTowerHitPoints": 9201,
  "princessTowersHitPoints": [6104, 6104],
  "clan": { "tag": "#GP8292Y8", "name": "Miyake YT", "badgeId": 16000054 },
  "cards": [],
  "supportCards": [],
  "elixirLeaked": 3.33,
  "globalRank": null,
  "startingTrophies": 12286,
  "trophyChange": 26
}
```

Verified fields:

- `tag`
- `name`
- `crowns`
- `kingTowerHitPoints`
- `princessTowersHitPoints`
- `clan?`
- `cards`
- `supportCards`
- `elixirLeaked`
- `globalRank`
- `startingTrophies?`
- `trophyChange?`
- `rounds?`

Conditional notes:

- `kingTowerHitPoints` and `princessTowersHitPoints` are the hitpoints _remaining_ when the battle ended — a
  margin-of-victory signal, not a tower level and not a maximum. Do not read them as progression or compare them across
  players as if they were levels.
- Both hit-point fields can also be `null` (observed live 2026-09: `princessTowersHitPoints: null` on a regular 1-crown
  ladder loss where a surviving princess tower is certain). Treat null as "the game did not report tower data for this
  battle" — it carries no information about tower state.
- `princessTowersHitPoints` shape (observed June–September 2026, ~50,000 rows): on head-to-head rows a destroyed tower
  is omitted, so length runs 2 → 1, and the field is `null` whenever no princess tower survives (all 2-crown-conceded
  and king-fallen rows) plus a few 1-crown rows. A `0` entry never appears on head-to-head rows. On duel rows destroyed
  towers can appear as `0` (`[0, 0]`, `[0, n]`) and length-1 arrays also occur, so array length is not a tower count
  there. See [Duel Rounds](#duel-rounds).
- `startingTrophies` appears on PvP, Path of Legend, river race PvP, river race duel, friendly, and clanmate battles.
- `trophyChange` appears only on PvP and Path of Legend battles.
- `globalRank` is present on all battles and is null unless the player is globally ranked.
- `supportCards` is always an array and may be empty.
- `cards` can also be empty (`[]`) on `type=trail` event-challenge battles: the API discloses no deck for some event
  formats. Observed 2026-09-15 on 1,976 recorded participants, all `trail`, June 2026. An empty list is not a deck
  identity - do not hash or compare it as one.
- On `type=boatBattle` entries the defending side's `cards` is the 12-card boat-defense list, not a played deck, and its
  `evolutionLevel` is ownership-style (can be `3`). See [players.md](../players.md) on `evolutionLevel`.
- `clan` is absent if the player has no clan.
- `rounds` appears only on river race duel battles (`riverRaceDuel` and `riverRaceDuelColosseum`).

`cards[*].evolutionLevel` is played-as state for that battle, not collection ownership. See
[players.md](players.md#evolution-fields).

## Duel Rounds

Used in `riverRaceDuel` and `riverRaceDuelColosseum` battles.

```json
{
  "crowns": 3,
  "kingTowerHitPoints": 7032,
  "princessTowersHitPoints": [4424, 3959],
  "elixirLeaked": 2.1,
  "cards": []
}
```

Fields:

- `crowns`
- `kingTowerHitPoints`
- `princessTowersHitPoints`
- `elixirLeaked`
- `cards`

Cards in duel rounds include an additional `used` boolean. Each round has a different deck. Rounds arrays usually
contain 2-3 rounds, and the participant's top-level `cards` is all rounds concatenated, not a deck.

A duel is ONE battle-log row for up to three games, and the participant's top-level fields inherit that (observed
June–September 2026, 412 duel rows):

- top-level `crowns` is the sum across rounds, up to 9 (134 of 412 rows carried more than 3; maximum seen 7);
- top-level `kingTowerHitPoints` / `princessTowersHitPoints` describe the final round only — a participant with
  earlier-round crowns can still finish at king `0`, princess `[0, 0]`;
- per-round `crowns` and tower hit points sit inside `rounds[*]`.

## CHAOS Modifiers

`modifiers` appears on CHAOS mode battles, currently `type=trail` with `Crazy_Arena`.

```json
[
  { "tag": "#PU9RCVYUG", "modifiers": ["Pekka3", "Graveyard2", "Rage1"] },
  { "tag": "#2JVGV9CG9", "modifiers": ["Fireball3", "GoblinHut2", "Berserker1"] }
]
```
