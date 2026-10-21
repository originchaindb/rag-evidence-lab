# Deploying rag-evidence-lab

## Development and production

Start with the synthetic fixture and a separate Cloud Free namespace. Free was chosen for low-cost development; verify current quotas, availability, backups and support against your own production requirements. These examples do not establish an SLA or performance benchmark.

Build an immutable CLI/container in CI, run its tests, and invoke it from a trusted job worker. `run` is offline; `save` adds Cloud persistence. The included Dockerfile runs as a non-root user and copies no secrets. Supply environment variables at runtime with your deployment secret manager. Do not bake `.env` into an image.

## Identity and data

Authenticate the caller in your API before invoking this code. Derive tenant/group identity on the server, never from a model response or browser field. Separate database namespaces or instances by environment; namespaces are naming isolation, not an authorization control. Limit which callers can read stored reports.

Collect only necessary data. Reports may contain excerpts, document IDs or feedback. Set a retention policy, perform access reviews, and test a backup/restore and deletion procedure before ingesting customer information. The sample's random run IDs avoid accidental overwrite; they do not provide immutable audit storage.

## Reliability

The adapter validates configuration, requires HTTPS, refuses redirects, limits input/response sizes, and reports sanitized errors. It does not retry writes automatically. A timeout or degraded replication means the write outcome may be uncertain: reconcile by run ID before resubmitting. Configure rate limiting, bounded retries with jitter for safe reads, quotas, and monitoring in your worker.

Schema registration is a development convenience. Use one initializer per fresh namespace. Verify the schema on startup and manage production changes as reviewed migrations. Never run competing initializers against an unclaimed namespace.

Database persistence and external side effects are not atomic. If you add email, payments, tickets or tool execution, use an outbox/reconciliation design and provider idempotency keys. Do not treat a local decision or saved report as authorization to act.

## Operational checklist

- Pin and scan dependencies; rerun tests on Linux and Windows after updates.
- Store keys in a secret manager, rotate them through the console, and verify revoked keys stop working.
- Record run IDs, status, duration and counts; omit authorization headers, source text and upstream response bodies from logs.
- Alert on authentication failures, rate limits, failures and unexpectedly high data volume.
- Re-run domain evaluation cases with realistic inputs; add failure and adversarial examples.
- Load test your expected input sizes and concurrency. The provided tests are functional checks, not a scalability claim.

## Project-specific review

Deterministic evidence checks do not prove semantic entailment. Maintain human-reviewed cases and review paraphrases manually.
