# Clash Royale API – Model Reference

---

## Players

| Model | Used By |
|-------|---------|
| `Player` | `GET /players/{playerTag}` |
| `PlayerClan` | nested in `Player` |
| `PlayerLeagueStatistics` | nested in `Player` |
| `LeagueSeasonResult` | nested in `PlayerLeagueStatistics` |
| `PathOfLegendSeasonResult` | nested in `Player` (current/last/best) |
| `PlayerItemLevel` / `PlayerItemLevelList` | `currentDeck`, `cards`, `supportCards` in `Player` |
| `PlayerAchievementProgress` / `PlayerAchievementProgressList` | nested in `Player` |
| `PlayerAchievementBadge` / `PlayerAchievementBadgeList` | nested in `Player` |
| `Arena` | nested in `Player`, `ClanMember` |
| `Item` | `currentFavouriteCard` in `Player`; prize type in challenges |
| `BattleList` / `Battle` | `GET /players/{playerTag}/battlelog` |
| `PlayerBattleData` / `PlayerBattleDataList` | nested in `Battle` |
| `PlayerBattleRound` / `PlayerBattleRoundList` | nested in `Battle` |
| `PlayerBattleAugment` / `PlayerBattleAugmentList` | nested in `Battle` |
| `UpcomingChests` / `ChestList` / `Chest` | `GET /players/{playerTag}/upcomingchests` |
| `Replay` | nested in `Battle` |

---

## Clans

| Model | Used By |
|-------|---------|
| `Clan` | `GET /clans/{clanTag}`, `GET /clans` |
| `ClanList` | `GET /clans` |
| `ClanMember` / `ClanMemberList` | `GET /clans/{clanTag}/members`, nested in `Clan` |
| `CurrentClanWar` | `GET /clans/{clanTag}/currentwar` |
| `ClanWarClan` / `ClanWarClanList` | nested in `CurrentClanWar` |
| `ClanWarParticipant` / `ClanWarParticipantList` | nested in `CurrentClanWar` |
| `ClanWarLog` / `ClanWarLogEntry` | `GET /clans/{clanTag}/warlog` |
| `ClanWarStanding` / `ClanWarStandingList` | nested in `ClanWarLogEntry` |

---

## River Race

| Model | Used By |
|-------|---------|
| `CurrentRiverRace` | `GET /clans/{clanTag}/currentriverrace` |
| `RiverRaceClan` / `RiverRaceClanList` | nested in `CurrentRiverRace` |
| `RiverRaceParticipant` / `RiverRaceParticipantList` | nested in `RiverRaceClan` |
| `PeriodLog` / `PeriodLogList` | nested in `CurrentRiverRace` |
| `PeriodLogEntry` / `PeriodLogEntryList` | nested in `PeriodLog` |
| `PeriodLogEntryClan` | nested in `PeriodLogEntry` |
| `RiverRaceLog` / `RiverRaceLogEntry` | `GET /clans/{clanTag}/riverracelog` |
| `RiverRaceStanding` / `RiverRaceStandingList` | nested in `RiverRaceLogEntry` |

---

## Rankings & Locations

| Model | Used By |
|-------|---------|
| `Location` / `LocationList` | `GET /locations`, `GET /locations/{locationId}` |
| `PlayerRanking` / `PlayerRankingList` | `/locations/{id}/rankings/players`, `/seasons/{id}/rankings/players` |
| `PlayerRankingClan` | nested in `PlayerRanking` |
| `ClanRanking` / `ClanRankingList` | `/locations/{id}/rankings/clans`, `/rankings/clanwars` |
| `PlayerPathOfLegendRanking` / `PlayerPathOfLegendRankingList` | `/locations/{id}/pathoflegend/players`, `/pathoflegend/{seasonId}/rankings/players` |
| `LeagueSeason` / `LeagueSeasonList` | `GET /locations/global/seasons`, `/seasonsV2` |
| `LadderTournamentRanking` / `LadderTournamentRankingList` | `GET /locations/global/rankings/tournaments/{tag}` |

---

## Leaderboards

| Model | Used By |
|-------|---------|
| `Leaderboard` / `LeaderboardList` | `GET /leaderboards`, `GET /leaderboard/{id}` |

---

## Tournaments

| Model | Used By |
|-------|---------|
| `Tournament` | `GET /tournaments/{tournamentTag}` |
| `TournamentHeader` / `TournamentHeaderList` | `GET /tournaments` |
| `TournamentMember` / `TournamentMemberList` | nested in `Tournament` |
| `GameMode` | nested in `Tournament` |
| `LadderTournament` / `LadderTournamentList` | `GET /globaltournaments` |

---

## Challenges

| Model | Used By |
|-------|---------|
| `ChallengeChain` / `ChallengeChainsList` | `GET /challenges` |
| `Challenge` / `ChallengeList` | nested in `ChallengeChain` |
| `ChallengeGameMode` | nested in `Challenge` |
| `SurvivalMilestoneReward` / `SurvivalMilestoneRewardList` | nested in `Challenge` |

---

## Cards & Events

| Model | Used By |
|-------|---------|
| `Items` | `GET /cards` — contains `items` (standard cards) and `supportItems` (Tower Troops) |
| `ItemList` / `Item` | nested in `Items`; fields: `name`, `id`, `maxLevel`, `maxEvolutionLevel`, `elixirCost`, `rarity`, `iconUrls` |
| `TrailEvent` | `GET /events` — returned as bare JSON array (no wrapper object) |
| `Emote` / `EmoteList` | not exposed via a documented endpoint |

---

## Utility & Primitives

| Model | Notes |
|-------|-------|
| `ClientError` | Universal error response: `{ reason, message, type, detail }` |
| `Version` | API version metadata |
| `Fingerprint` | Device/session fingerprint |
| `JsonNode` | Generic untyped JSON node — treat as `any` |
| `JsonLocalizedName` | Localized name wrapper |
| `Match` / `RegisterMatchRequest` / `RegisterMatchResponse` / `CancelMatchResponse` | Match registration — likely private/partner API |
| `VerifyTokenRequest` / `VerifyTokenResponse` | Token verification |
| `StringList` / `String` / `IntegerList` / `Integer` / `Float` | Primitive wrappers |

---

## Agent Notes
- `List` suffix types (e.g. `ClanMemberList`) are always arrays of their singular counterpart
- `Match`, `RegisterMatchRequest/Response`, and `CancelMatchResponse` have no documented public endpoints — likely internal or partner-only
- `Emote`/`EmoteList` similarly has no documented endpoint — may be embedded in other responses
- `JsonNode` fields should be treated as opaque until inspected at runtime

