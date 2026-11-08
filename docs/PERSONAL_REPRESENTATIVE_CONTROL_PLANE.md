# Personal Representative Control Plane (HRCP) — v0.1

## Purpose

HRCP owns the representative lifecycle and coordinates identity, consent, capability evidence, authority, approval and evidence. It is the control boundary between an AI representative and any future execution adapter.

## Lifecycle

CONFIGURED → ACTIVE ↔ PAUSED → REVOKED

- Registration requires a verified owner identity, a distinct representative ID, at least one owner-approved knowledge reference and mandatory AI disclosure.
- Activation requires current service-processing consent and a non-revoked, unexpired authority contract bound to the same owner and representative.
- Pause raises the stop switch, invalidates outstanding approvals and marks queued work cancelled.
- Revocation is terminal in this reference implementation. A new representative identity is required for a new delegation lifecycle.

## Admission sequence

1. Resolve the representative under the authenticated owner.
2. Confirm state ACTIVE and stop switch clear.
3. Match the expected representative version.
4. Confirm current service-processing consent.
5. Confirm tested AI capability for the exact capability and data scope.
6. Confirm authority contract identity, ID and version.
7. For high-impact or irreversible work, verify a short-lived, one-time approval bound to task digest, owner, representative version and authority version.
8. Re-evaluate authority and append evidence.
9. Return an admission decision. This module does not execute the side effect.

## Approval binding and replay resistance

An approval is not a general “yes”. It is bound to a canonical digest of task type, tool, data scopes and impact flags. It also binds owner, representative version, authority contract ID/version and expiry. Successful admission consumes the approval once. Pause or revocation invalidates outstanding approvals.

## Stop and revocation

The process-local stop switch is checked for every admission. Pause/revoke cancels tasks registered in the in-memory pending set. Production must store stop state durably and check it atomically at the side-effect boundary; queued jobs, retries and workers must re-check immediately before execution. The stop path must not depend on the model provider.

## Trust and implementation limits

This is a deterministic, standard-library reference implementation, not a production security boundary. Owner IDs are caller-supplied identifiers here; production must authenticate and authorize every owner action. State, approvals and pending tasks are in memory and are lost on restart. A single process lock does not provide distributed consistency. There is no database, API, worker, cryptographic signature, secure clock, key management, rate limiting or tool execution.

The side_effect_permitted field intentionally remains false even when admission returns ALLOW. A later execution gateway must perform a fresh authorization check immediately before any side effect and independently enforce the stop switch, current consent, scope and idempotency.
