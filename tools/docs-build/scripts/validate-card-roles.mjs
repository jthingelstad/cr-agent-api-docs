#!/usr/bin/env node
/**
 * Guard the deck-archetype vocabulary (data/card-roles.json and
 * data/deck-aliases.json). These files are read by other programs to
 * name decks, so a malformed entry is a wrong name served with
 * authority. Every entry needs a public source (a URL), a family from
 * the closed set, and a role shape the grammar understands. The seed
 * entries are guarded by name: an attested win condition cannot vanish
 * in a rewrite.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const read = (rel) => JSON.parse(readFileSync(path.join(repo, rel), "utf8"));

const FAMILIES = new Set(["beatdown", "control", "cycle", "bait", "bridge_spam", "siege"]);
const failures = [];
const fail = (m) => failures.push(m);

const roles = read("data/card-roles.json");
const seen = new Set();
for (const r of roles.roles ?? []) {
  const where = `card-roles ${r.id} ${r.name ?? ""}`.trim();
  if (!Number.isInteger(r.id) || r.id < 26000000) fail(`${where}: id is not a catalog card id`);
  if (seen.has(r.id)) fail(`${where}: duplicate id`);
  seen.add(r.id);
  if (typeof r.name !== "string" || !r.name) fail(`${where}: name missing`);
  if (typeof r.source !== "string" || !/https?:\/\//.test(r.source)) fail(`${where}: source must cite a public URL`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(r.attested_at ?? "")) fail(`${where}: attested_at is not a date`);
  const isWinCon = r.tier !== undefined || r.bait_tiers !== undefined;
  if (isWinCon) {
    if (r.tier !== null && r.tier !== undefined && typeof r.tier !== "number") fail(`${where}: tier must be a number or null`);
    if (!FAMILIES.has(r.family)) fail(`${where}: family '${r.family}' is not one of ${[...FAMILIES].join(", ")}`);
    if (r.at_cycle_cost !== undefined && !FAMILIES.has(r.at_cycle_cost)) fail(`${where}: at_cycle_cost is not a family`);
    if (r.bait_tiers !== undefined) {
      if (r.tier !== null && r.tier !== undefined) fail(`${where}: a bait win condition has bait_tiers, not a tier`);
      for (const [k, v] of Object.entries(r.bait_tiers))
        if (!/^\d+$/.test(k) || typeof v !== "number") fail(`${where}: bait_tiers is {minimum count: tier}`);
    } else if (typeof r.tier !== "number") fail(`${where}: a win condition needs a tier`);
    for (const p of r.pairs_with ?? []) {
      if (!Number.isInteger(p.id)) fail(`${where}: pairs_with entry without an id`);
      if (p.family !== undefined && !FAMILIES.has(p.family)) fail(`${where}: pairs_with family is not a family`);
    }
  } else if (r.bait_unit !== true && r.bridge_partner !== true) {
    fail(`${where}: an entry is a win condition, a bait unit or a bridge partner`);
  }
  for (const flag of ["bait_unit", "bridge_partner", "needs_partner"])
    if (r[flag] !== undefined && r[flag] !== true) fail(`${where}: ${flag} is true or absent`);
}
for (const u of roles.unattested ?? []) {
  if (seen.has(u.id)) fail(`card-roles unattested ${u.id}: listed as unattested but has a role`);
}
// Seed win conditions that a rewrite must not drop.
for (const [id, name] of [
  [26000021, "Hog Rider"], [26000059, "Royal Hogs"], [27000008, "X-Bow"], [27000002, "Mortar"],
  [26000009, "Golem"], [26000029, "Lava Hound"], [28000010, "Graveyard"], [28000004, "Goblin Barrel"],
  [26000004, "P.E.K.K.A"], [26000032, "Miner"], [26000006, "Balloon"], [26000024, "Royal Giant"],
]) {
  const r = (roles.roles ?? []).find((x) => x.id === id);
  if (!r || (r.tier === undefined && r.bait_tiers === undefined)) fail(`card-roles: ${name} (${id}) is no longer a win condition`);
}

const aliases = read("data/deck-aliases.json");
const aliasKeys = new Set();
for (const a of aliases.aliases ?? []) {
  const where = `deck-aliases '${a.alias}'`;
  const key = String(a.alias ?? "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  if (!key) fail(`${where}: alias missing`);
  if (aliasKeys.has(key)) fail(`${where}: duplicate alias (after normalisation)`);
  aliasKeys.add(key);
  if (!Array.isArray(a.cards) || a.cards.length === 0 || !a.cards.every(Number.isInteger)) fail(`${where}: cards must be catalog ids`);
  if (a.family !== null && !FAMILIES.has(a.family)) fail(`${where}: family '${a.family}' is not a family or null`);
  if (typeof a.source !== "string" || !/https?:\/\//.test(a.source)) fail(`${where}: source must cite a public URL`);
}

if (failures.length) {
  for (const f of failures) console.error(f);
  process.exit(1);
}
console.log(`Validated ${(roles.roles ?? []).length} card role(s) and ${(aliases.aliases ?? []).length} deck alias(es).`);
