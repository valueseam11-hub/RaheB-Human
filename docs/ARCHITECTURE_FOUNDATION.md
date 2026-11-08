# RaheB Human — Architecture Foundation v0.1

## Product boundary

A Personal Professional Representative (PPR) is an AI system operating transparently as an AI under a human owner's identity context, approved knowledge, bounded delegation and human oversight. It is not the human, does not impersonate the human, and does not inherit the human's professional licence, credentials or authority.

## Foundation layers

1. **Human identity:** verified owner identity and account lifecycle.
2. **Representative identity:** distinct AI instance, version and disclosure state.
3. **Personal intelligence:** owner-approved knowledge, professional preferences and versioned memory.
4. **Capability registry:** independently tested AI capabilities, each bound to a task scope, test-suite version and evidence.
5. **Authority and delegation:** versioned contract naming owner, representative, tasks, tools, data scopes, approval rules, expiry and revocation.
6. **Consent and information rights:** purpose-specific consent for service processing, persistent memory, analytics, model training and employer sharing.
7. **Execution gateway:** policy check before every side effect; missing or uncertain authority means HOLD.
8. **Evidence and provenance:** trace of source, representative version, authority version, capability assessment, approvals, tool invocation and outcome.
9. **Security and privacy:** tenant isolation, encryption, secret brokering, document scanning, redaction, retention and deletion controls.
10. **Professional and organization interfaces:** employer/client boundaries, portability and explicit human contribution attribution.

## Mandatory action sequence

Identity and representative version → task intake → data-purpose/consent check → source retrieval → capability fit check → authority admission → plan → human review where required → tool execution through constrained gateway → outcome capture → evidence record.

A later production implementation must re-check authority immediately before the side effect, not only when a task is queued. Revocation, expiry, changed scope or changed representative version invalidates pending admission. Queue cancellation and race conditions require dedicated integration tests.

## Authority contract

The contract is a machine-enforceable delegation, not a blanket permission. It must include:
- owner and representative identifiers;
- contract ID and version;
- permitted task types, tools and data scopes;
- prohibited tasks and mandatory approval conditions;
- effective time, expiry and revocation state;
- organization, employer and client data boundaries;
- accountability and evidence requirements.

High-impact or irreversible actions require explicit human approval by default. Financial approvals, contract acceptance, legal/medical decisions, hiring/firing, public commitments, government filings and safety-critical actions remain outside autonomous execution in this foundation.

## Evidence semantics

Evidence records should distinguish ASSERTED, CONFIGURED, TESTED and OBSERVED. A cryptographic digest can help detect record changes; it does not establish that the content is true, that a source was authoritative, or that an action is currently authorized. Production requires signed records, key rotation, trusted timestamps, durable append-only storage, access controls and independent verification.

## Initial product wedge

Start with a professional operations representative for approved-document analysis, reconciliation preparation, reporting, research and draft preparation. Use synthetic data for engineering tests. Do not connect live employer/client data until tenant isolation, consent enforcement, retention, incident response and security review are complete.

## Deferred infrastructure

FastAPI API layer, PostgreSQL with row-level security, OIDC/WebAuthn identity, policy decision point, secrets broker, malware scanning, observability, model gateway and durable workflow orchestration are subsequent integration milestones. This v0.1 package intentionally remains standard-library Python so the authority rules can be tested independently of vendors.
