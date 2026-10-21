# Verification — 21 October 2026

**Local tests and real OriginChainDB Cloud Free checks passed.** This release ran as a native Python CLI on Windows. The database was the actual hosted Free instance; no local database substituted for it. The console showed Free, Running and No charge. A data API connection alone does not establish plan type.

See the [sanitized receipt](verification.json), [test cases](../tests), [input fixture](../examples/input.json), and [observed output](../examples/expected.json).

| Check | Result |
| --- | --- |
| Domain and failure-case tests | Passed |
| Native runnable example | Passed; matches examples/expected.json |
| Schema registration and existing-schema verification | Passed against Cloud Free |
| Save report and read through a fresh client | Passed against Cloud Free |
| SQL list includes saved run ID | Passed against Cloud Free |
| Separate process retrieves identical saved report | Passed against Cloud Free |
| Paid model calls in this release | None |
| Container build / hosted app | Not tested / not deployed |

The synthetic input deliberately includes failed domain checks. A report containing a denial or review reason is expected; successful execution is not a claim that every fixture passes its domain criteria.

Claude response parsing and the persistent three-attempt allowance are covered with synthetic tests. No live Claude generation is claimed for this release.

Only synthetic reports were uploaded. Each project used an isolated namespace and retained its small verification record. Temporary credentials were removed before publishing; they are absent from source, fixtures and receipts. GitHub Actions results are visible on the repository Actions tab after publishing; a local pass is not a claim that remote CI has already finished.

## Limits of this evidence

Deterministic evidence checks do not prove semantic entailment. Maintain human-reviewed cases and review paraphrases manually.

These are functional checks, not a load test, penetration test, production SLA, immutable audit guarantee or evidence that a model is always correct. Review [production guidance](PRODUCTION.md) before deployment.
