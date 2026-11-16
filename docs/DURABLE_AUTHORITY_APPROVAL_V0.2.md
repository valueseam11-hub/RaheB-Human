# Durable Authority & Exact Approval — RaheB Human v0.2

## What changed

This milestone adds a persistent authority record layer to the existing synthetic FastAPI application's SQLite database.

- Immutable, version-bound authority warrants.
- Append-only revocation records; parent revocation invalidates descendant warrants during admission.
- Human approvals bound to the exact warrant digest, representative version, action, resource, purpose, task reference and SHA-256 output digest.
- Single-use approval consumption under SQLite's write transaction.
- Cumulative money and token reservations per warrant.
- Hash-chained authority events with update/delete database triggers.
- Authenticated owner identity is taken from the existing server session, never request JSON.
- Organisation-sourced warrant issuance fails closed until organisation identity and administrator authority are implemented.

## Safety behavior

A successful admission consumes an approval and reserves budget, but returns `side_effect_permitted=false`. It does not invoke a model, tool, payment provider, email service, browser, workplace connector or external agent. No production data or live work is enabled.

## Persistence boundary

SQLite persistence survives process restarts on the configured local database file and uses a serialized write transaction for single-use consumption. It is not a multi-node/distributed production store. The current PostgreSQL tenant-isolation work is separate and not assumed to be integrated; this PR does not silently merge it or claim PostgreSQL runtime support.

## Important limitations

- The current demo route is the only enabled route for issuing owner warrants and approvals.
- Organisation authority is explicitly unavailable; the two-key model is documented but not falsely represented as complete.
- No cryptographic authorizer signature, hardware-backed key, secure timestamp authority, distributed revocation cache, external credential cancellation, settlement/refund reconciliation or real execution gateway exists.
- A digest binds bytes, not truth, identity or competence.
- Budget reservation is an admission record, not a provider-side spending cap. It cannot prevent spend outside a future controlled adapter.
- No deployment or live action is included.

## Next production gates

1. Reconcile and test PostgreSQL tenant schema and runtime adapter.
2. Bind authenticated owner identity and separately verified organisation administrator identity.
3. Move warrant, approval, revocation and budget transactions to a tenant-isolated PostgreSQL store with atomic row locking.
4. Sign warrants/approvals with managed keys and define key rotation/revocation.
5. Integrate a gateway at every actual side-effect boundary, with provider-level spend ceilings, idempotency and cancellation/reconciliation adapters.
6. Conduct concurrency, replay, tenant-isolation and failure-injection testing before enabling any real execution.
