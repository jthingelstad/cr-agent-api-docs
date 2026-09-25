# Player Models

Player-related field shapes verified against live API responses (March-April 2026).

## Player

Used by `GET /players/{playerTag}`.

Verified fields:

| Field                                                                                             | Notes                                                                                                                                                                                                                      |
| ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tag`, `name`                                                                                     | Player identity                                                                                                                                                                                                            |
| `expLevel`, `expPoints`, `totalExpPoints`, `starPoints`                                           | Legacy account progression — Experience Level was retired in-game in 2026; see [players.md](../players.md)                                                                                                                 |
| `trophies`, `bestTrophies`                                                                        | Trophy Road values. The Trophy Road ceiling is **14,000** — a legitimate max that real accounts sit at, not a sentinel or a capture bug. Do not treat high values as bad data; older ~9,000 ceiling assumptions are wrong. |
| `arena`                                                                                           | [Arena](common.md#arena)                                                                                                                                                                                                   |
| `role`                                                                                            | Optional clan role                                                                                                                                                                                                         |
| `wins`, `losses`, `battleCount`, `threeCrownWins`                                                 | Battle totals                                                                                                                                                                                                              |
| `donations`, `donationsReceived`, `totalDonations`                                                | Donation counters                                                                                                                                                                                                          |
| `challengeCardsWon`, `challengeMaxWins`, `tournamentCardsWon`, `tournamentBattleCount`            | Challenge and tournament counters                                                                                                                                                                                          |
| `warDayWins`, `clanCardsCollected`                                                                | Legacy war counters                                                                                                                                                                                                        |
| `currentWinLoseStreak`                                                                            | Optional signed streak counter                                                                                                                                                                                             |
| `clan`                                                                                            | Optional [PlayerClan](common.md#playerclan)                                                                                                                                                                                |
| `leagueStatistics`                                                                                | Optional `PlayerLeagueStatistics`                                                                                                                                                                                          |
| `currentDeck`, `cards`, `currentDeckSupportCards`, `supportCards`                                 | Player card arrays                                                                                                                                                                                                         |
| `currentFavouriteCard`                                                                            | Catalog-like `Item` object; not reliably player-settable (no liveness challenges)                                                                                                                                          |
| `badges`, `achievements`                                                                          | Progress and account markers                                                                                                                                                                                               |
| `currentPathOfLegendSeasonResult`, `lastPathOfLegendSeasonResult`, `bestPathOfLegendSeasonResult` | Nullable `PathOfLegendSeasonResult`                                                                                                                                                                                        |
| `legacyTrophyRoadHighScore`                                                                       | Nullable integer                                                                                                                                                                                                           |
| `progress`                                                                                        | Map of side-mode season IDs to progress objects                                                                                                                                                                            |

Optional Player fields, absent when not applicable:

- `clan`
- `role`
- `leagueStatistics`
- `currentWinLoseStreak`

Nullable Player fields, always present but null when not applicable:

- `currentPathOfLegendSeasonResult`
- `lastPathOfLegendSeasonResult`
- `bestPathOfLegendSeasonResult`
- `legacyTrophyRoadHighScore`

## PlayerLeagueStatistics

```json
{
  "currentSeason": { "trophies": 12530, "bestTrophies": 6650 },
  "previousSeason": {
    "id": "2026-02",
    "rank": 3288,
    "trophies": 7163,
    "bestTrophies": 7250
  },
  "bestSeason": { "id": "2021-02", "rank": 926, "trophies": 7506 }
}
```

Notes:

- `currentSeason` has no `id` or `rank`.
- `currentSeason.bestTrophies` is optional and can be absent early in a season.
- `previousSeason.bestTrophies` is optional.
- `previousSeason` and `bestSeason` include `id` in `YYYY-MM` format and optional `rank`.

## PathOfLegendSeasonResult

Fields:

- `leagueNumber` - integer; 1-7 on current and last results. `bestPathOfLegendSeasonResult` can also carry 8-10 (29.9%
  of non-null bests, March-September 2026) from an earlier season whose league scale ran higher. Current and last never
  exceeded 7 on any archived profile. Never read a best against the current seven leagues.
- `trophies` - integer
- `rank` - integer or null

The parent season-result field itself can be null for players without Path of Legend history.

## PlayerItemLevel

Used by `currentDeck`, `cards`, `currentDeckSupportCards`, and `supportCards`.

Fields:

- `name`
- `id`
- `level`
- `starLevel?`
- `evolutionLevel?`
- `maxLevel`
- `maxEvolutionLevel?`
- `rarity`
- `count`
- `elixirCost?`
- `iconUrls`

`count` is copies currently held in inventory. It is volatile and can be `0` for maxed or currently equipped cards.

## Item

Used by the card catalog and `currentFavouriteCard`.

Fields:

- `name`
- `id`
- `maxLevel`
- `maxEvolutionLevel?`
- `elixirCost?`
- `iconUrls`
- `rarity`

## Evolution Fields

`maxEvolutionLevel` describes static card capability:

| Value  | Meaning                          |
| ------ | -------------------------------- |
| `1`    | Evo-capable                      |
| `2`    | Hero-capable                     |
| `3`    | Supports both Evo and Hero modes |
| absent | No alternate mode                |

`evolutionLevel` is context-sensitive:

| Appears in                                       | Meaning                                                                 |
| ------------------------------------------------ | ----------------------------------------------------------------------- |
| `cards[]`                                        | Ownership: the player has this mode unlocked                            |
| `currentDeck[]`                                  | Deployment: the card is currently slotted to play as the indicated mode |
| battle-log `team[*].cards` / `opponent[*].cards` | Played-as state in that battle                                          |

Value mapping:

| Value  | Meaning                                                                                                          |
| ------ | ---------------------------------------------------------------------------------------------------------------- |
| `1`    | Evo                                                                                                              |
| `2`    | Hero                                                                                                             |
| `3`    | Evo + Hero, observed only in `cards[]`                                                                           |
| absent | No unlocked alternate mode in `cards[]`, or not configured/played as an alternate mode in deck and battle arrays |

Both fields are bit fields (bit 1 = Evo, bit 2 = Hero; `3` = `1 | 2`), never an ordinal or a progress counter:
`evolutionLevel=2` with `maxEvolutionLevel=3` means Hero unlocked and Evo not, not "2 of 3". The catalog's `iconUrls`
corroborate the bit assignment on all 123 standard cards (2026-09-09, see [../cards.md](../cards.md)).

Verified empirically across 15,442 live battles (April 2026): `evolutionLevel` appears on only 2-3 slots per battle,
slot positions match evo/hero slot mechanics, and `evolutionLevel=3` was not observed in deck or battle arrays.

For ownership checks, read `cards[]`. For deployment or played-as checks, read `currentDeck[]` or battle-log card
arrays.

## Card Level Interpretation

`level` and `maxLevel` use the API's rarity-relative scale, not a universal cross-rarity scale.

| Rarity      | API levels | Normalized levels |
| ----------- | ---------: | ----------------: |
| `common`    |     `1-16` |            `1-16` |
| `rare`      |     `1-14` |            `3-16` |
| `epic`      |     `1-11` |            `6-16` |
| `legendary` |      `1-8` |            `9-16` |
| `champion`  |      `1-6` |           `11-16` |

Conversion:

- `common`: `normalized = level`
- `rare`: `normalized = level + 2`
- `epic`: `normalized = level + 5`
- `legendary`: `normalized = level + 8`
- `champion`: `normalized = level + 10`

## Badges

Progress badge:

```json
{
  "name": "Grand12Wins",
  "level": 5,
  "maxLevel": 8,
  "progress": 150,
  "target": 250,
  "iconUrls": { "large": "..." }
}
```

One-time badge:

```json
{ "name": "Crl20Wins2021", "progress": 20, "iconUrls": { "large": "..." } }
```

One-time badges omit `level`, `maxLevel`, and `target` entirely. They are not present as `null`.

A tiered badge at its top tier also omits `target` while keeping `level` and `maxLevel` (8.5% of archived tiered badge
entries, March-September 2026; in a one-clan sample, exactly the ones at `level == maxLevel`). So `target` absence does
not identify a one-time badge; `level` absence does.

Badge categories observed:

- Mastery badges, such as `MasteryKnight` - tiered, with `maxLevel` 10 (all 68 Mastery badges on one recorded profile,
  2026-09-25)
- Challenge badges, such as `Classic12Wins`
- Mode badges, such as `2v2`, `RampUp`, `SuddenDeath`, `Draft`, `2xElixir`
- Collection badges, such as `EmoteCollection`, `BannerCollection`, `CollectionLevel`, `ClanDonations`
- Seasonal badges, such as `SeasonalBadge_202507_v2`
- Event badges, such as `CrlSpectator2022` and `EasterEgg`
- Career badges, such as `YearsPlayed`, `BattleWins`, `ClanWarsVeteran`, `LadderTop1000`
- League and trail badges, in pairs: `<Mode>Completion` and `<Mode>Rank` for `CrazyArena`, `TripleDraftLeague`,
  `SuddenDeathTrail`, `AnarchyLeague`, `ChaosDraftLeague`, `RoyalTournament`, `ClassicRoyaleTournament` and `2v2League`
  (archived profiles, March-September 2026; the last pair, `2v2LeagueCompletion` / `2v2LeagueRank`, first seen
  2026-09-21). For `RoyalTournament` and `ClassicRoyaleTournament` the Rank badge also occurs as a `_v2` twin. Also
  seen: `RouletteAllModes` (first seen 2026-09-21) and `Chaos_S2`.

**`name` is an internal identifier, not a display name.** A badge carries no player-facing name anywhere in the API;
only `iconUrls` is what the game shows. Anything that prints a badge to a person has to translate. Observed across 1,773
recorded profiles (survey 2026-09-19, 200 distinct badge names):

- **Mastery badges are `Mastery` + the card's INTERNAL name**, which is the card's shown name with spaces removed for
  most cards (`MasteryHogRider`, `MasteryThreeMusketeers`, `MasteryGoblinstein`) and an older codename for the rest.
  Codenames observed, cross-checked against community card data (`sc_key`): `SkeletonWarriors` = Guards, `Archer` =
  Archers, `IceSpirits` = Ice Spirit, `FireSpirits` = Fire Spirit, `ZapMachine` = Sparky, `MiniSparkys` = Zappies,
  `RageBarbarian` = Lumberjack, `AxeMan` = Executioner, `IceGolemite` = Ice Golem, `BlowdartGoblin` = Dart Goblin,
  `AngryBarbarians` = Elite Barbarians, `Assassin` = Bandit, `DarkWitch` = Night Witch, `WitchMother` = Mother Witch,
  `Ghost` = Royal Ghost, `MovingCannon` = Cannon Cart, `SkeletonBalloon` = Skeleton Barrel, `DartBarrell` = Flying
  Machine, `EliteArcher` = Magic Archer, `FirespiritHut` = Furnace, `BarbLog` = Barbarian Barrel, `Heal` = Heal Spirit,
  `Snowball` = Giant Snowball, `Xbow` = X-Bow, `Log` = The Log, `Pekka` / `MiniPekka` = P.E.K.K.A / Mini P.E.K.K.A,
  `Wallbreakers` = Wall Breakers. Three newer codenames are inferred by elimination (the only three Mastery badges with
  no matching card, against the only three cards with no Mastery badge), not confirmed: `GiantBuffer` = Rune Giant,
  `DarkMagic` = Void, `MergeMaiden` = Spirit Empress.
- **One Mastery name carries a literal space:** `MasteryElixir Collector` (observed 2026-09-19, 1,460 holders). Do not
  assume badge names are single tokens.
- **Dated badges suffix `_YYYYMM`**, sometimes with a revision: `SeasonalBadge_202509`, `SeasonalBadge_202507_v2`,
  `MergeTacticsBadge_202506`. A `_v2` twin of an undated badge also occurs (`RoyalTournamentRank` and
  `RoyalTournamentRank_v2` both observed, each tiered to 10) - treat them as distinct badges, not one renamed.
- **Yearly and numbered badges:** `2025YearBadge` (one-off) and `2026YearBadge` (tiered, max 6) differ in shape across
  years; `CrazyArenaBadge1/2/3` are three one-off badges, not levels of one.
- **CRL badges** pin a year: `Crl20Wins2019`..`Crl20Wins2025` plus an undated `Crl20Wins`; `CrlSpectator2022/2024/2025`;
  `CrlFinalist2024/2025`; `CrlChampion2024/2025`; `CrlCompetitor2022`. Rare one-offs observed once each:
  `SupercellEmployee`, `Creator`, `SupercellPancake`.

Two badges are load-bearing for account progression:

- `CollectionLevel` — since the game's 2026 Collection Level update, its `progress` is the player's current Collection
  Level (the progression number the game shows), while `level`/`maxLevel` are the badge's own tier. The top-level
  `collectionLevel` field (first present 2026-07-31) was at first a zero-valued stub, but a sampled current profile
  returned `2036` on 2026-09-13, exactly matching its badge's `progress`; use the top-level field on current profiles
  and this badge as a cross-check. Treat an older zero or an absent field as legacy payload shape, never as a real
  level. Collection Level is the SUM of the levels of every card the player owns, plus 5 for each Evolution and each
  Hero form unlocked, so it is a four-digit number (observed 1673) and only ever rises. It is independent of King Tower
  Level, which is a separate ~1-16 value earned by upgrading required counts of cards.
- `YearsPlayed` — its `level` is the number of completed years the account has existed, and its `progress` is the
  account age in days (observed live: level 4 / progress 1648 / target 1825 — targets are 365-day tiers). The badge
  first appears at one year, so absence USUALLY means a sub-1-year account — but not always: a 74-profile sweep
  (2026-09) found 2 accounts carrying a `Royals2v2_2024` event badge with no `YearsPlayed`. Treat a missing badge as
  unknown, not zero, and never infer "new player" from absence alone.

## Achievements

```json
{
  "name": "Team Player",
  "stars": 3,
  "value": 1717,
  "target": 1,
  "info": "Join a Clan",
  "completionInfo": null
}
```

Fields:

- `name`
- `stars` - integer `0-3`
- `value`
- `target`
- `info`
- `completionInfo` - typically null

Known achievements: Team Player, Friend in Need, Road to Glory, Gatherer, TV Royale, Tournament Rewards, Tournament
Host, Tournament Player, Challenge Streak, Practice with Friends, Special Challenge, Friend in Need II.

## Chest

Used by `GET /players/{playerTag}/upcomingchests`.

```json
{ "index": 0, "name": "Gold Crate" }
```

Indices are non-contiguous because only notable chests are listed.

Observed names include Gold Crate, Plentiful Gold Crate, Overflowing Gold Crate, Golden Chest, Magical Chest, Giant
Chest, Epic Chest, Legendary Chest, Mega Lightning Chest, Royal Wild Chest, and Tower Troop Chest.

## Progress

```json
{
  "": {
    "arena": {
      "id": 168000059,
      "name": "Diamond",
      "rawName": "AutoChessArena10_2025_Oct"
    },
    "trophies": 4257,
    "bestTrophies": 4337
  },
  "AutoChess_2026_Mar": { "arena": { ... }, "trophies": 3460, "bestTrophies": 3593 }
}
```

`progress` is a map of opaque mode-season IDs to arena/trophy data. Do not treat the key names as a stable enum.

A bucket's `arena.rawName` always belongs to the bucket's own mode and season (`AutoChess_2026_Season_11` →
`AutoChessArena<N>_2026_Season_11`, `TripleDraftTrail` → `TripleDraftArena<N>`), across 206,926 archived buckets,
March-September 2026. The `""` bucket always carries `AutoChessArena<N>_2025_Oct`: it is Merge Tactics' October 2025
season under an empty key, present on all but 6 of 57,185 profile payloads. Event-league buckets (`CrazyArena`,
`TripleDraftTrail`, `SuddenDeathTrail`, `AnarchyLeague`) were each seen for three weeks or less; the map is not a
permanent history.
