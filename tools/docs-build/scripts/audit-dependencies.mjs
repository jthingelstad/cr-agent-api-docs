#!/usr/bin/env node
/** Jamie's approved development-only GHSA-fc5q-39xc-vjpf exception.
 * The production audit remains a separate, exception-free npm command.
 * See ../AUDIT.md. This gate is intentionally local to this build tool.
 */
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ADVISORY = "https://github.com/advisories/GHSA-fc5q-39xc-vjpf";
const LEVELS = ["info", "low", "moderate", "high", "critical"];
const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const elevated = (level) => LEVELS.indexOf(level) >= LEVELS.indexOf("high");
const docsRoot = fileURLToPath(new URL("../", import.meta.url));

/** Classify the whole graph, including below-threshold sibling branches.
 * Only an exact accepted high leaf can exempt its high dependants, and
 * every reported installation on those branches must be dev:true.
 */
export function classifyAudit(report, lockfile) {
  if (
    !object(report) ||
    report.auditReportVersion !== 2 ||
    report.error ||
    !object(report.vulnerabilities) ||
    !object(lockfile?.packages)
  )
    throw new Error("Unrecognized audit report or lockfile");
  const graph = report.vulnerabilities;
  const resolved = new Map();
  function visit(name, ancestry = new Set()) {
    if (ancestry.has(name)) throw new Error(`Cyclic audit dependency: ${name}`);
    if (resolved.has(name)) return resolved.get(name);
    const entry = Object.hasOwn(graph, name) ? graph[name] : null;
    if (
      !object(entry) ||
      entry.name !== name ||
      !LEVELS.includes(entry.severity) ||
      !Array.isArray(entry.via) ||
      entry.via.length === 0 ||
      !Array.isArray(entry.nodes) ||
      entry.nodes.length === 0 ||
      !entry.nodes.every((node) => typeof node === "string" && node.length > 0)
    )
      throw new Error(`Invalid audit entry: ${name}`);
    const next = new Set([...ancestry, name]);
    const state = {
      acceptedCause: false,
      otherHigh: entry.severity === "critical",
      devOnly: entry.nodes.every(
        (node) => Object.hasOwn(lockfile.packages, node) && lockfile.packages[node]?.dev === true,
      ),
    };
    for (const cause of entry.via) {
      if (typeof cause === "string") {
        const child = visit(cause, next);
        state.acceptedCause ||= child.acceptedCause;
        state.otherHigh ||= child.otherHigh;
        state.devOnly &&= child.devOnly;
      } else {
        if (
          !object(cause) ||
          cause.name !== name ||
          cause.dependency !== name ||
          !LEVELS.includes(cause.severity) ||
          typeof cause.url !== "string" ||
          typeof cause.range !== "string"
        )
          throw new Error(`Invalid audit advisory: ${name}`);
        if (!elevated(cause.severity)) continue;
        const exact =
          name === "picomatch" &&
          entry.severity === "high" &&
          cause.severity === "high" &&
          cause.url === ADVISORY &&
          cause.range === "<=4.0.7";
        state.acceptedCause ||= exact;
        state.otherHigh ||= !exact;
      }
    }
    // A high entry without the approved cause is never an exception.
    if (elevated(entry.severity) && !state.acceptedCause) state.otherHigh = true;
    resolved.set(name, state);
    return state;
  }
  const accepted = [],
    blocked = [];
  for (const [name, entry] of Object.entries(graph)) {
    const state = visit(name);
    if (!elevated(entry.severity)) {
      if (state.acceptedCause || state.otherHigh) throw new Error(`Invalid audit severity: ${name}`);
      continue;
    }
    (entry.severity === "high" && state.acceptedCause && !state.otherHigh && state.devOnly ? accepted : blocked).push(
      name,
    );
  }
  return { accepted: accepted.sort(), blocked: blocked.sort() };
}

/** A failed process or inconsistent severity/exit status is not a clean audit. */
export function checkAuditRun(run, lockfile) {
  if (run.error || run.signal || ![0, 1].includes(run.status)) throw new Error("npm audit did not complete normally");
  const result = classifyAudit(JSON.parse(run.stdout), lockfile);
  const findings = result.accepted.length + result.blocked.length;
  if (run.status !== (findings ? 1 : 0)) throw new Error("npm audit exit status disagrees with its findings");
  if (result.blocked.length) throw new Error(`Unaccepted high/critical findings: ${result.blocked.join(", ")}`);
  return result;
}

function main() {
  const run = spawnSync("npm", ["audit", "--json", "--audit-level=high"], {
    cwd: docsRoot,
    encoding: "utf8",
    maxBuffer: 8 * 1024 * 1024,
    stdio: ["ignore", "pipe", "inherit"],
  });
  const lockfile = JSON.parse(readFileSync(new URL("../package-lock.json", import.meta.url), "utf8"));
  const result = checkAuditRun(run, lockfile);
  if (result.accepted.length)
    console.log(`Approved development-only exception: ${ADVISORY}\nAffected packages: ${result.accepted.join(", ")}`);
  console.log("Dependency audit passed.");
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    main();
  } catch (error) {
    console.error(`Dependency audit failed: ${error.message}`);
    process.exitCode = 1;
  }
}
