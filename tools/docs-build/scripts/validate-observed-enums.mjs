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
 * Inherited from a downstream project (elixir-bot), which had been carrying
 * this guard against its own vendored copy of these docs. The copy is gone;
 * the guard belongs with the docs it guards.
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
  ["players.md", "`kingTowerLevel`", "the profile field that replaced the expLevel-derived King Tower"],
  ["players.md", "`unknown`", "the deckSelection value seen on an event-tagged mode"],
  ["models/battles.md", "- `unknown`", "unknown as a battle type"],
  ["models/players.md", "14,000", "the real Trophy Road ceiling"],
  ["clans.md", "19691231T235959.000Z", "the epoch-zero finishTime sentinel"],
  ["clans.md", "Waiting for Clan War to start", "the 404 window between races"],
  ["models/river-race.md", "category error", "fame vs periodPoints are not interchangeable"],
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
