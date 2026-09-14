# Leaderboard Models

Leaderboard field shapes verified against live API responses (March 2026; metadata nullability September 14, 2026).

## Leaderboard Metadata

Used by `GET /leaderboards`.

```json
{ "id": 170000019, "name": "Merge Tactics" }
```

Fields:

- `id` - integer
- `name` - string or `null`

Observed September 14, 2026: `GET /leaderboards` returned 30 metadata objects, including 15 explicit null names. Every
object contained the `name` key. A null name is different from an absent field; preserve the numeric `id` for discovery
and do not infer that the board is disabled or that its battle history is exposed from its name alone.

Multiple leaderboards can share the same name with different IDs.

## Leaderboard Ranking Entry

Used by `GET /leaderboard/{leaderboardId}`.

```json
{
  "tag": "#PU9RCVYUG",
  "name": "FJ21",
  "rank": 1,
  "score": 4047,
  "clan": { "tag": "#GP8292Y8", "name": "Miyake YT", "badgeId": 16000054 }
}
```

Fields:

- `tag`
- `name`
- `rank`
- `score`
- `clan?`

`clan` is absent when the player has no clan.

`GET /leaderboard/{leaderboardId}` can return up to 10,000 entries when no `limit` is specified.
