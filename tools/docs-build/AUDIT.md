# Docs tooling dependency audit

Jamie approved on 2026-11-17 (US Central):

> Approved: extend the exact development-only picomatch exception to cr-agent-api-docs.

The full dependency audit keeps its high-severity threshold. Its one exception is
[GHSA-fc5q-39xc-vjpf](https://github.com/advisories/GHSA-fc5q-39xc-vjpf), for `picomatch` at high severity with the
reported affected range exactly `<=4.0.7`. High dependent findings are covered only when that advisory is their sole
elevated cause, every reported installation in their dependency branches has literal `dev: true` in the lockfile, and no
entry is critical. Ordinary low/moderate sibling findings remain below the existing threshold; they are not additional
risk exceptions. Their branches are still checked for hidden high findings, missing metadata and production
installations.

Production dependencies use an independent `npm audit --omit=dev --audit-level=low`, without any exception. Every other
high or critical advisory fails the full audit. Unknown report versions, malformed or cyclic dependencies, missing
lockfile paths, audit execution errors and inconsistent exit status fail closed. The required `validate` gate remains.

The local controls, production audit and full audit are:

```sh
npm --prefix tools/docs-build run test:audit
npm audit --prefix tools/docs-build --omit=dev --audit-level=low
npm --prefix tools/docs-build run audit:dependencies
```

No dependency version is downgraded or otherwise changed for this exception. Remove the exception and its dedicated
classifier when a patched picomatch release is available and the lockfile is updated so the ordinary full audit passes.
The [upstream advisory](https://github.com/advisories/GHSA-fc5q-39xc-vjpf) is the source for patch availability.
