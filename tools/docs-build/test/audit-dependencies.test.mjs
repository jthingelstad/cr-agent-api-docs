import { test } from "node:test";
import assert from "node:assert/strict";
import { classifyAudit, checkAuditRun } from "../scripts/audit-dependencies.mjs";

const acceptedUrl = "https://github.com/advisories/GHSA-fc5q-39xc-vjpf";
const leaf = (name, severity, url, range = "*") => ({ name, dependency: name, severity, url, range });
function fixture() {
  const vulnerabilities = {
    picomatch: {
      name: "picomatch",
      severity: "high",
      nodes: ["node_modules/picomatch", "node_modules/other/node_modules/picomatch"],
      via: [leaf("picomatch", "high", acceptedUrl, "<=4.0.7")],
    },
    fdir: { name: "fdir", severity: "high", nodes: ["node_modules/fdir"], via: ["picomatch"] },
    tinyglobby: {
      name: "tinyglobby",
      severity: "high",
      nodes: ["node_modules/tinyglobby"],
      via: ["fdir", "picomatch"],
    },
    minimatch: {
      name: "minimatch",
      severity: "moderate",
      nodes: ["node_modules/minimatch"],
      via: [leaf("minimatch", "moderate", "https://github.com/advisories/GHSA-g3hv-75wg-m249")],
    },
    "markdownlint-cli": {
      name: "markdownlint-cli",
      severity: "high",
      nodes: ["node_modules/markdownlint-cli"],
      via: ["minimatch", "tinyglobby"],
    },
  };
  const report = { auditReportVersion: 2, vulnerabilities };
  const lock = {
    packages: Object.fromEntries(
      Object.values(vulnerabilities).flatMap((v) => v.nodes.map((node) => [node, { dev: true }])),
    ),
  };
  return { report, lock, graph: vulnerabilities };
}
const run = (report, status = 1) => ({ status, signal: null, stdout: JSON.stringify(report) });

test("accepts exactly the development-only advisory and its high dependent chains", () => {
  const { report, lock } = fixture();
  const result = checkAuditRun(run(report), lock);
  assert.deepEqual(result, { accepted: ["fdir", "markdownlint-cli", "picomatch", "tinyglobby"], blocked: [] });
  assert.ok(!result.accepted.includes("minimatch"), "a moderate sibling is below threshold, not another exception");
});

test("a clean report needs no exception; the existing full-audit threshold stays high", () => {
  const { report, lock, graph } = fixture();
  assert.deepEqual(checkAuditRun(run({ ...report, vulnerabilities: {} }, 0), lock), { accepted: [], blocked: [] });
  assert.deepEqual(checkAuditRun(run({ ...report, vulnerabilities: { minimatch: graph.minimatch } }, 0), lock), {
    accepted: [],
    blocked: [],
  });
});

for (const path of [
  "node_modules/picomatch",
  "node_modules/other/node_modules/picomatch",
  "node_modules/fdir",
  "node_modules/minimatch",
  "node_modules/markdownlint-cli",
]) {
  for (const dev of [false, undefined, "true"])
    test(`refuses a non-development installation on any accepted branch: ${path} ${dev}`, () => {
      const { report, lock } = fixture();
      lock.packages[path].dev = dev;
      assert.throws(() => checkAuditRun(run(report), lock), /Unaccepted high\/critical/);
    });
}

test("a missing lock installation cannot be presumed development-only", () => {
  const { report, lock } = fixture();
  delete lock.packages["node_modules/picomatch"];
  assert.throws(() => checkAuditRun(run(report), lock), /Unaccepted/);
});

for (const [field, value] of [
  ["url", "https://github.com/advisories/GHSA-other"],
  ["range", "<=4.0.8"],
  ["severity", "critical"],
])
  test(`pins the accepted advisory's ${field}`, () => {
    const { report, lock, graph } = fixture();
    graph.picomatch.via[0][field] = value;
    assert.throws(() => checkAuditRun(run(report), lock), /Unaccepted/);
  });

test("critical aggregate escalation is rejected even with the accepted high leaf", () => {
  const { report, lock, graph } = fixture();
  graph.fdir.severity = "critical";
  const result = classifyAudit(report, lock);
  assert.ok(result.blocked.includes("fdir"));
  assert.ok(result.blocked.includes("markdownlint-cli"));
  assert.throws(() => checkAuditRun(run(report), lock), /Unaccepted/);
});

test("the moderate sibling becoming high is not covered by picomatch acceptance", () => {
  const { report, lock, graph } = fixture();
  graph.minimatch.severity = "high";
  graph.minimatch.via[0].severity = "high";
  const result = classifyAudit(report, lock);
  assert.ok(result.blocked.includes("minimatch"));
  assert.ok(result.blocked.includes("markdownlint-cli"));
});

test("a below-threshold entry cannot hide another high advisory", () => {
  const { report, lock, graph } = fixture();
  graph.minimatch.via[0].severity = "high";
  assert.throws(() => checkAuditRun(run(report), lock), /Invalid audit severity|Unaccepted/);
});

test("a high aggregate without an accepted advisory cause is rejected", () => {
  const { report, lock, graph } = fixture();
  graph["markdownlint-cli"].via = ["minimatch"];
  assert.throws(() => checkAuditRun(run(report), lock), /Unaccepted/);
});

for (const change of [
  (g) => {
    g.fdir.via = ["missing"];
  },
  (g) => {
    g.picomatch.via = ["fdir"];
  },
  (g) => {
    g.fdir.via = [];
  },
  (g) => {
    g.fdir.nodes = [];
  },
  (g) => {
    g.fdir.nodes = [null];
  },
  (g) => {
    g.fdir.severity = "unknown";
  },
  (g) => {
    g.fdir.name = "different";
  },
  (g) => {
    g.picomatch.via = [{}];
  },
  (g) => {
    g.minimatch.via = [null];
  },
])
  test("unknown, missing, cyclic or malformed graph data fails closed", () => {
    const { report, lock, graph } = fixture();
    change(graph);
    assert.throws(() => checkAuditRun(run(report), lock));
  });

for (const report of [
  null,
  {},
  { auditReportVersion: 1 },
  { auditReportVersion: 2, vulnerabilities: [] },
  { auditReportVersion: 2, vulnerabilities: {}, error: { code: "NETWORK" } },
])
  test("unknown or failed audit report is never a passing audit", () => {
    assert.throws(() => checkAuditRun(run(report), { packages: {} }));
  });

for (const result of [
  { status: null },
  { status: 2 },
  { status: 0, error: new Error("network") },
  { status: 1, signal: "SIGTERM" },
  { status: 0, stdout: "{" },
  { status: 1, stdout: JSON.stringify({ auditReportVersion: 2, vulnerabilities: {} }) },
])
  test("audit execution errors and inconsistent exit status fail closed", () => {
    const { report, lock } = fixture();
    assert.throws(() => checkAuditRun({ ...run(report), ...result }, lock));
  });

test("exit zero with high findings fails closed too", () => {
  const { report, lock } = fixture();
  assert.throws(() => checkAuditRun(run(report, 0), lock), /exit status/);
});

test("a standalone below-threshold entry cannot conceal a high advisory in a zero-exit report", () => {
  const { report, lock, graph } = fixture();
  graph.minimatch.via[0].severity = "high";
  assert.throws(() => checkAuditRun(run({ ...report, vulnerabilities: { minimatch: graph.minimatch } }, 0), lock));
});
