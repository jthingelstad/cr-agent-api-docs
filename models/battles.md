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
observed in any of 1,062,672 archived battle-log entries, March-September 2026; treat them as official-only.

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
- `unknown` (the All Random Princess modes, which disclose no deck)

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

## `trail` means "this battle belongs to an event", and `eventTag` says which

This is the cleanest rule in the battle log, and it is exact. Over 370k recorded battles (2026-09-22):

| type                                                      | battles | carry `eventTag`                      |
| --------------------------------------------------------- | ------- | ------------------------------------- |
| `trail`                                                   | 123,562 | **100.0%**                            |
| `pathOfLegend`                                            | 186,948 | 0.0%                                  |
| `PvP`                                                     | 36,742  | 0.0%                                  |
| `riverRacePvP`                                            | 12,198  | 0.0%                                  |
| `friendly`                                                | 6,022   | 0.0%                                  |
| `riverRaceDuel` / `riverRaceDuelColosseum` / `boatBattle` | 6,444   | 0.0%                                  |
| `tournament`                                              | 2,144   | 0.0% (but 100% carry `tournamentTag`) |
| `clanMate`                                                | 2,581   | 62.2%                                 |
| `clanMate2v2`                                             | 366     | 71.0%                                 |
| `unknown`                                                 | 1,900   | 91.6%                                 |

So `type: "trail"` is not a game mode and not a format: it is **the marker that a battle was played inside a time-bound
event**, and the permanent formats never carry one. `tournament` is the same pattern with `tournamentTag`. A `clanMate`
battle carries an `eventTag` when the friendly was played under an event's ruleset.

**The event, not the mode, is the population.** Supercell slots an event into a `gameMode` for a date window, and REUSES
the pair later for a different event:

| type · gameMode · eventTag       | battles | window                  | active days |
| -------------------------------- | ------- | ----------------------- | ----------- |
| trail · TeamVsTeam · `#2C9J990U` | 67,475  | 2026-09-07 → 2026-09-21 | 15          |
| trail · TeamVsTeam · `#2RC8CL00` | 1,690   | 2026-08-03 → 2026-09-07 | 36          |
| trail · TeamVsTeam · `#2PRCGVPP` | 1,180   | 2026-06-01 → 2026-07-06 | 36          |
| trail · TeamVsTeam · `#2928CY0P` | 952     | 2026-05-04 → 2026-06-01 | 29          |
| trail · Ladder · `#2C9JG9GP`     | 10,719  | 2026-09-07 → 2026-09-22 | 16          |
| trail · Ladder · `#2RC8C0JU`     | 1,920   | 2026-08-03 → 2026-09-07 | 36          |

`trail`+`TeamVsTeam` alone carries **ten** distinct event tags, `trail`+`Showdown_Friendly` twelve. So a pair like
"trail, TeamVsTeam" is a slot, not an identity - the September burst above (68-680 battles a day until 09-06, 3,976 on
09-07, a 40,680 peak on 09-20, 372 on 09-22) is the September 2026 2v2 League, `#2C9J990U`, not a property of the pair.
Its battles are stamped with the league's own arenas (`2v2League_202609Arena1`/`Arena2`: 89,769 archived entries,
2026-09-07 to 2026-09-24, exactly the tag's). The profile tracks it in the `2v2League_202609` progress bucket, and the
`2v2LeagueCompletion` / `2v2LeagueRank` badges first appear on 2026-09-21, the day the burst ended.

Two window shapes recur. The **36-day** ones land exactly on season boundaries (`#2RC8C0JU` runs 2026-08-03 to
2026-09-07, which is season 135 to the day; `#2PRCGVPP` runs 2026-06-01 to 2026-07-06, season 133) - a recurring format
re-tagged each season. The shorter ones are one-off events. An `eventTag` can also span more than one (type, gameMode):
`#2C9JG9GP` appears on both `trail`+`Ladder` and `clanMate`+`Friendly`, one event offering several ways to play it.

**For a consumer:** never pool an `eventTag`-bearing battle with a permanent format, and never pool two event tags
because they share a mode name. `eventTag` is date-bound by construction, which is what makes it the right key.

## `trail` is the Seasonal Trophy Road, and its card levels are not the player's

`type: "trail"` is not a legacy value and not a party-mode bucket, though it collects those too. Since the **June 2026
update** it is overwhelmingly the reworked **Seasonal Trophy Road** - the Seasonal Road, with Seasonal Arena I (your own
deck) and Seasonal Arena II (your eight most-won-with cards banned, and low cards boosted to a minimum Level 15).

Observed in a 370k-battle record (2026-09-22), counting battles whose `gameMode.name` is `Ladder`, the `trail`-typed
ones begin in **June 2026** and are absent before it:

| month              | `type: PvP`           | `type: trail` |
| ------------------ | --------------------- | ------------- |
| 2026-03 to 2026-05 | 4,377 / 6,407 / 4,909 | 0             |
| 2026-06            | 4,678                 | 323           |
| 2026-07            | 5,322                 | 555           |
| 2026-08            | 5,269                 | 1,049         |
| 2026-09            | 5,458                 | 11,653        |

**Do not read a game-wide migration from those monthly totals.** They are one recorder's corpus, and its population
changed by six times in September (23,895 distinct players in August, 140,943 in September) toward players who play Path
of Legends and the Seasonal Road rather than Trophy Road. The reliable claim is the START DATE - nothing before June
2026 - and the per-battle evidence below, which is measured within a population rather than across months.

Two consequences for any consumer:

1. **It behaves like Trophy Road on trophies.** A `trail` Ladder loss deducts (12,993 of 13,578 losses carry a negative
   `trophyChange`, against 35,033 of 36,716 for `PvP`), and wins award. So trophy mechanics will NOT tell these apart,
   and a "seasonal trophies do not deduct" rule from an older limited-time Trail event does not hold here.
2. **The card levels are the format's, not the player's.** Mean recorded deck level is **15.87 on `trail` Ladder against
   13.67 on `PvP` Ladder**; the median is exactly **16.00**, and **99.9%** of `trail` decks sit at 14.5 or above against
   52.8% for `PvP`. That is Seasonal Arena II's Level 15 floor. Pooling the two populations for a card-level, level-gap
   or deck-strength comparison measures the arena, not the player.

**The same bucket holds permanent formats and two-week events, which is the strongest argument for keying on the pair.**
Inside `type: trail`, `gameMode: Ladder` is a permanent seasonal format running at a steady 1,000-2,700 battles a day,
while `gameMode: TeamVsTeam` was the September 2v2 League: 68-680 battles a day through 2026-09-06, then 3,976 on 09-07,
climbing to a peak of 40,680 on 09-20, 24,948 on 09-21, and **372 on 09-22** - back to baseline the day it ended. A
consumer that groups on `type` alone pools a permanent ladder with a fortnight's league and sees neither.

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
  "tag": "#PLAYER1",
  "name": "Player One",
  "crowns": 3,
  "kingTowerHitPoints": 9201,
  "princessTowersHitPoints": [6104, 6104],
  "clan": { "tag": "#CLAN1", "name": "Clan One", "badgeId": 16000054 },
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
- `startingTrophies?` (on pathOfLegend only in league 7; see [players.md](../players.md))
- `trophyChange?` (on pathOfLegend leagues 1-6 only on a win, always `+30`; see [players.md](../players.md))
- `rounds?`

Conditional notes:

- `kingTowerHitPoints` and `princessTowersHitPoints` are the hitpoints _remaining_ when the battle ended — a
  margin-of-victory signal, not a tower level and not a maximum. Do not read them as progression or compare them across
  players as if they were levels.
- `princessTowersHitPoints` can also be `null` (observed live 2026-09 on a regular 1-crown ladder loss where a surviving
  princess tower is certain). Treat null as "the game did not report tower data for this battle" — it carries no
  information about tower state. `kingTowerHitPoints` is always an integer at the participant level (never null or
  absent in 2.37 million archived participant entries, March-September 2026; `0` when the King Tower fell).
- `princessTowersHitPoints` shape (observed June–September 2026, ~50,000 rows): on head-to-head rows a destroyed tower
  is omitted, so length runs 2 → 1, and the field is `null` whenever no princess tower survives (all 2-crown-conceded
  and king-fallen rows) plus a few 1-crown rows. A `0` entry never appears on head-to-head rows. On duel rows destroyed
  towers can appear as `0` (`[0, 0]`, `[0, n]`) and length-1 arrays also occur, so array length is not a tower count
  there. See [Duel Rounds](#duel-rounds).
- `startingTrophies` appears on PvP, Path of Legend, river race PvP, river race duel, friendly, and clanmate battles.
- `trophyChange` appears only on PvP and Path of Legend battles.
- `globalRank` is present on all battles and is null unless the player is globally ranked.
- `supportCards` is always an array and may be empty.
- `cards` can also be empty (`[]`): the API discloses no deck for the All Random Princess modes
  (`deckSelection: unknown`, 72000501 and 72000519). Observed on every one of 14,130 archived entries of those modes,
  June-September 2026, and on no other mode's team side. An empty list is not a deck identity - do not hash or compare
  it as one.
- On `type=boatBattle` entries the defending side's `cards` is the 12-card boat-defense list, not a played deck, and its
  `evolutionLevel` is ownership-style (can be `3`). See [players.md](../players.md) on `evolutionLevel`.
- `clan` is absent if the player has no clan.
- `rounds` appears on every best-of-3 duel: `riverRaceDuel`, `riverRaceDuelColosseum` and the 1v1 Duel friendly
  (`Duel_1v1_Friendly` 72000314, `deckSelection: quadDeckPick`). Observed March-September 2026 on 15,614 archived
  entries, all of them duels.

`cards[*].evolutionLevel` is played-as state for that battle, not collection ownership. See
[players.md](players.md#evolution-fields).

## Duel Rounds

Used in river race duels and in `Duel_1v1_Friendly`.

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
- `kingTowerHitPoints?`
- `princessTowersHitPoints`
- `elixirLeaked`
- `cards`

Round tower fields differ from the participant's. A round's `princessTowersHitPoints` always holds two entries (`0` for
a destroyed tower) and is never `null` (36,732 archived rounds per side, March-September 2026). Its `kingTowerHitPoints`
is absent, not `0`, in a round where the opponent took three crowns (all 108 such rounds in a one-clan sample of 1,038,
July-September 2026, and present on every other round).

Cards in duel rounds include an additional `used` boolean. Each round has a different deck. Rounds arrays usually
contain 2-3 rounds, and the participant's top-level `cards` is all rounds concatenated, not a deck.

A duel is ONE battle-log row for up to three games, and the participant's top-level fields inherit that (observed
June–September 2026, 412 duel rows):

- top-level `crowns` is the sum across rounds, up to 9 (134 of 412 rows carried more than 3; maximum seen 7);
- top-level `kingTowerHitPoints` / `princessTowersHitPoints` describe the final round only — a participant with
  earlier-round crowns can still finish at king `0`, princess `[0, 0]`;
- per-round `crowns` and tower hit points sit inside `rounds[*]`.

## CHAOS Modifiers

`modifiers` appears on every battle of the seven CHAOS rulesets and on no other: `Crazy_Arena` (72000502),
`Crazy_Arena_EpicOnly` (72000504), `Crazy_Arena_InfiniteElixir` (72000510), `Crazy_Arena_SuddenDeath` (72000511),
`Chaos_1v1_Draft` (72000505), `Chaos_1v1_TripleDraft` (72000506) and `Chaos_1v1_MegaDraft_All` (72000512). This holds
whatever the `type` (`trail`, `friendly`, `unknown`); observed March-September 2026 on 66,914 archived entries. It holds
one element per participant. Each lists 1-6 modifiers, 4 most often, not a fixed three. A modifier is
`<card codename><tier 1-3>` using the Mastery badge codenames: `AxeMan2` is Executioner at tier 2 (see
[players.md](players.md#badges)).

```json
[
  { "tag": "#PLAYER1", "modifiers": ["Pekka3", "Graveyard2", "Rage1", "AxeMan2"] },
  { "tag": "#PLAYER2", "modifiers": ["Fireball3", "GoblinHut2", "Berserker1", "Assassin1"] }
]
```
