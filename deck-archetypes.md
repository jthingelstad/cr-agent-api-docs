# Deck Archetypes

How players name decks, and the vocabulary a program needs to name one the same way. The API carries no archetype field
and the game names nothing; this is community usage, written down with a source per fact so a deck can be named
identically by every caller. The machine-readable form is [data/card-roles.json](data/card-roles.json) (which cards are
win conditions, bait units, bridge partners) and [data/deck-aliases.json](data/deck-aliases.json) (the community names
the grammar below does not produce). The docs build validates both: a public URL on every entry, a family from the
closed set, and the long-standing win conditions cannot be dropped in a rewrite.

## Two layers, kept apart

**Families** are a small, stable taxonomy that deck sites filter on and guides teach: **beatdown, control, cycle, bait,
bridge spam, siege**. Some guides add "hybrid"; here a deck has one family and may have two win conditions, which is how
a hybrid shows.

**Named decks** — "2.6 Hog Cycle", "LavaLoon", "PEKKA Ghost bridge spam", "Splashyard" — are hand-curated titles for
particular card sets. Deck Shop titles every exact deck by hand; RoyaleTracker lists eleven with descriptors and states
no rules; the Fandom wiki has `Deck:` pages. No site publishes an algorithm for them. They are recorded here only as
**aliases**, so a program can understand a name a person uses; a program should not assert one.

| Family      | Definition (the community's)                                                                                                  | Attested                                                                                                                                                                                                                   |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| beatdown    | build a large push behind a high-hitpoint tank; accept elixir deficits to overwhelm                                           | [Red Bull](https://www.redbull.com/us-en/win-with-right-archetype-clash-royale), [GamingOnPhone](https://gamingonphone.com/guides/clash-royale-deck-archetypes/), [TrophyCoach](https://trophycoach.com/tools/deck-finder) |
| control     | defend efficiently, counter-push, chip; win over time                                                                         | GamingOnPhone, TrophyCoach                                                                                                                                                                                                 |
| cycle       | cheap cards, fast rotation back to a chip win condition; guides quote "under 3.5" average elixir, the named decks run 2.6–3.1 | all guides; [Modern Hog Cycle](https://clashroyale.fandom.com/wiki/Deck:Modern_Hog_Cycle)                                                                                                                                  |
| bait        | force the opponent's small spells with spell-vulnerable swarm, then punish                                                    | all guides; [RoyaleTracker](https://royaletracker.gg/best-decks/archetypes) (Log Bait)                                                                                                                                     |
| bridge spam | fast units at the bridge to deny the opponent a build-up and punish mistakes                                                  | [RoyaleAPI filter](https://royaleapi.com/decks/popular?lang=en&type=Archetype_BridgespamAny&time=7d), TrophyCoach                                                                                                          |
| siege       | attack the tower from one's own side with X-Bow or Mortar                                                                     | all guides; RoyaleAPI                                                                                                                                                                                                      |

## The grammar of a name

`<win condition> [<distinguishing card>] <family>` — "Royal Hogs bridge spam", "PEKKA Ghost bridge spam", "Hog cycle".
The family is sometimes elided when the win condition implies it ("Hog EQ", "Miner Poison") and sometimes the whole name
is a portmanteau ("LavaLoon", "Splashyard", "LumberLoon"). The average elixir is a prefix on cycle decks ("2.6 Hog",
"2.9 Mortar cycle"). The win condition's **form** is said — "Evo Hogs", "Evo Archers Pekka bridge spam" — but other
cards' forms are not.

A program composing a name from cards therefore needs, per card: whether it is a win condition and how strongly it
anchors a deck (a Golem names the deck before the Miner beside it), which family it implies (and whether a cheap build
flips that to cycle), whether it needs a bridge partner to be bridge spam rather than control, and which cards are bait
units. That is `data/card-roles.json`. The composition rules — priority, the bait-package test, the partner test, the
cycle and beatdown bounds — are the consuming program's, not this reference's.

## Where the community disagrees

- **Royal Hogs**: bridge spam to [TrophyCoach](https://trophycoach.com/tools/deck-finder) and the deck sites; bait to
  [GamingOnPhone](https://gamingonphone.com/guides/clash-royale-deck-archetypes/). The data file follows the deck sites.
- **X-Bow and Mortar at cycle cost**: "2.9 X-Bow cycle" and "2.9 Mortar cycle" are real names, and RoyaleAPI files both
  cards under siege regardless. The family here is siege; the names resolve by alias.
- **P.E.K.K.A and Mega Knight**: control in the guides, bridge spam on the deck sites — the difference is the partners
  beside them, so the file marks both as needing a bridge partner.
- **The cycle bound**: "under 3.5" in guides, tuned lower by some tools. A consumer should measure it on its own data
  and say what it used.

## Unattested cards

Cards in the catalog for which no public archetype attestation was found on the retrieval date are listed under
`unattested` in the data file, with no role. A deck built around one is named by its cost alone ("Beatdown", "Control",
"Cycle") until a source names it. Adding a role means adding a public source; the validator refuses an entry without
one.

## Maintenance

The vocabulary changes by accretion: a new card gets attested a few times a year, a rework occasionally turns a support
card into a win condition. It is not versioned by season — a role is a property of the card, not of the month it was
learned in, and a consumer relabelling its history when the vocabulary improves is correct. The file's git history is
the ledger.
