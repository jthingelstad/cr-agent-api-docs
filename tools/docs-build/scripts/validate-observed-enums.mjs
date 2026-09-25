#!/usr/bin/env node
/**
 * Guard the enum values we have actually SEEN on the wire.
 *
 * Observed values are the expensive part of this reference: each one cost a
 * real battle log, a real profile, or a real season rollover to find. Prose
 * gets rewritten and tables get reflowed, and an observed ID is easy to drop
 * by accident in the process. This fails the build if one goes missing.
 *
 * Only add an entry here once it has been observed on the wire and written
 * into the docs -- this asserts what we know, it does not wish for coverage.
 *
 * Inherited from a project that had been carrying this guard against its
 * own vendored copy of these docs. The copy is gone; the guard belongs with
 * the docs it guards.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const read = (rel) => readFileSync(path.join(repo, rel), "utf8");

// Battle-log gameMode ids observed on the wire, with their reported names.
const OBSERVED_GAME_MODES = [
  [72000011, "DoubleElixir_Friendly"],
  [72000033, "RampUpElixir_Friendly"],
  [72000051, "TeamVsTeam_Touchdown_Draft"],
  [72000060, "Overtime_Ladder"],
  [72000286, "TeamVsTeam_TripleElixir_Friendly"],
  [72000376, "Event_RestlessDead"],
  [72000501, "All_Random_Princess"],
  [72000504, "Crazy_Arena_EpicOnly"],
  [72000505, "Chaos_1v1_Draft"],
  [72000506, "Chaos_1v1_TripleDraft"],
  [72000510, "Crazy_Arena_InfiniteElixir"],
  [72000511, "Crazy_Arena_SuddenDeath"],
  [72000512, "Chaos_1v1_MegaDraft_All"],
];

// Free-text claims that must survive a rewrite, keyed to the file that owns them.
const OBSERVED_CLAIMS = [
  ["models/players.md", "`MasteryElixir Collector`", "a badge name with a literal space, observed 2026-09-19"],
  ["models/players.md", "`SkeletonWarriors` = Guards", "the Mastery badge codename that reads as code, observed 2026-09-19"],
  ["models/players.md", "`RoyalTournamentRank_v2`", "the _v2 twin of an undated badge, observed 2026-09-19"],
  ["models/leaderboards.md", "`name` - string or `null`", "leaderboard metadata name nullability observed 2026-09-14"],
  ["models/leaderboards.md", "15 explicit null names", "the 30-board metadata survey observed 2026-09-14"],
  [
    "index.md",
    "123 standard + 4 Tower Troops",
    "the standard and support catalog sizes observed 2026-09-08",
  ],
  [
    "cards.md",
    "55/123 standard cards",
    "the alternate-form capability count observed 2026-09-08",
  ],
  [
    "models/cards-events.md",
    "123 standard cards (observed 2026-09-17)",
    "the model catalog size re-observed 2026-09-17",
  ],
  [
    "models/cards-events.md",
    "4 Tower Troops (observed 2026-09-17)",
    "the model support catalog size re-observed 2026-09-17",
  ],
  ["players.md", "`kingTowerLevel`", "the profile field that replaced the expLevel-derived King Tower"],
  ["players.md", "`unknown`", "the deckSelection value seen on an event-tagged mode"],
  ["players.md", "`trophies: 14000`, `bestTrophies: 0`", "the seasonal-trophy-road progress bucket is not the player's trophies (observed 2026-09-17)"],
  ["models/battles.md", "- `unknown`", "unknown as a battle type"],
  ["models/battles.md", "sum across rounds, up to 9", "duel crowns are a sum across rounds (observed 2026-09)"],
  ["models/battles.md", "describe the final round only", "duel tower hit points are final-round only (observed 2026-09)"],
  ["cards.md", "normalized = level + (16 - maxLevel)", "the rarity-independent level normalization"],
  ["cards.md", "all 123 standard cards matched", "the form bit field corroborated by icon assets (2026-09-09)"],
  ["models/players.md", "14,000", "the real Trophy Road ceiling"],
  ["clans.md", "19691231T235959.000Z", "the epoch-zero finishTime sentinel"],
  [
    "clans.md",
    "`finishTime` is a war-day close",
    "finishTime is the war-day close the boat crossed on, not the week close (observed 2026-09-21)",
  ],
  [
    "clans.md",
    "The race-close time is per race, drawn at the season roll",
    "the close slot is per race, never one clan's clock (observed across six clans 2026-09-17)",
  ],
  ["clans.md", "Waiting for Clan War to start", "the 404 window between races"],
  ["models/river-race.md", "category error", "fame vs periodPoints are not interchangeable"],
  [
    "locations.md",
    "`eloRating` is the player's `currentPathOfLegendSeasonResult.trophies`",
    "the board rating equals the profile's PoL trophies (observed 2026-09-18)",
  ],
  [
    "locations.md",
    "capped at 1,000 places by the API, and the cap is a cut, not a floor",
    "the live PoL board's depth and the cursor probe past position 1000 (observed 2026-09-20)",
  ],
  [
    "locations.md",
    "ranks 9991–9999 all at `eloRating` 2342",
    "the season final's 9,999-place cut lands mid-tie (observed 2026-09-20)",
  ],
];

const failures = [];

const players = read("players.md");
for (const [id, name] of OBSERVED_GAME_MODES) {
  if (!players.includes(`| ${id} | ${name}`)) {
    failures.push(`players.md: observed game mode ${id} (${name}) is no longer documented`);
  }
}

for (const [file, needle, why] of OBSERVED_CLAIMS) {
  if (!read(file).includes(needle)) {
    failures.push(`${file}: lost "${needle}" — ${why}`);
  }
}

if (failures.length) {
  console.error("Observed-value guard failed:\n");
  for (const f of failures) console.error(`  - ${f}`);
  console.error(
    "\nThese were observed on the live API. If one is genuinely obsolete, remove it from" +
      "\ntools/docs-build/scripts/validate-observed-enums.mjs in the same commit and say why.",
  );
  process.exitCode = 1;
} else {
  console.log(
    `Validated ${OBSERVED_GAME_MODES.length} observed game mode(s) and ${OBSERVED_CLAIMS.length} observed claim(s).`,
  );
}
