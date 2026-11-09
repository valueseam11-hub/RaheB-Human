# RaheB Human — Architecture Foundation v0.2

## Product boundary

A Personal Professional Representative (PPR) is an AI system operating transparently as AI under a human owner's identity context, approved knowledge, bounded delegation and human oversight. It is not the human, does not impersonate the human, and does not inherit the human's professional licence, credentials or authority.

## Foundation layers

1. **Human identity:** verified owner identity and account lifecycle.
2. **Representative identity:** distinct AI instance, version and disclosure state.
3. **Personal intelligence:** source-attributed knowledge, owner approval, versioned memory and retrieval scoped to each task.
4. **Capability registry:** independently tested AI capabilities, each bound to a task scope, test-suite version and evidence.
5. **Authority and delegation:** versioned contract naming owner, representative, tasks, tools, data scopes, approval rules, expiry and revocation.
6. **Consent and information rights:** purpose-specific consent for service processing, persistent memory, analytics, model training and employer sharing.
7. **Execution gateway:** policy check before every side effect; missing or uncertain authority means HOLD.
8. **Evidence and provenance:** trace of source, content digest, representative version, authority version, capability assessment, approvals, tool invocation and outcome.
9. **Security and privacy:** tenant isolation, encryption, secret brokering, document scanning, redaction, retention and deletion controls.
10. **Professional and organization interfaces:** employer/client boundaries, portability and explicit human contribution attribution.

## Personal knowledge lifecycle

Owner-authorized source → ingestion under service + persistent-memory consent → source metadata and content digest → PENDING_REVIEW → explicit owner approval → APPROVED → scope-filtered retrieval → cited task context → outcome evidence. Withdrawal or consent withdrawal blocks future retrieval. New source versions are separate and require fresh approval.

Owner approval does not make embedded instructions trusted. Documents, emails, retrieved pages and extracted text remain untrusted data and cannot modify policy, authority or tool permissions.

## Mandatory action sequence

Identity and representative version → task intake → data-purpose/consent check → source retrieval → capability fit check → authority admission → plan → human review where required → tool execution through constrained gateway → outcome capture → evidence record.

A production implementation must re-check authority and stop state immediately before the side effect, not only when a task is queued.

## Authority contract

The contract is a machine-enforceable delegation, not blanket permission. It includes owner and representative identifiers; ID and version; permitted task types, tools and data scopes; prohibited tasks and mandatory approvals; effective time, expiry and revocation; organization/employer/client data boundaries; accountability and evidence requirements.

High-impact or irreversible actions require explicit human approval by default. Financial approvals, contract acceptance, legal/medical decisions, hiring/firing, public commitments, government filings and safety-critical actions remain outside autonomous execution in this foundation.

## Evidence semantics

Evidence records distinguish ASSERTED, CONFIGURED, TESTED and OBSERVED. A digest can help detect record changes; it does not establish truth, source authority or current authorization. Production requires signed records, key rotation, trusted timestamps, durable append-only storage, access controls and independent verification.

## Initial product wedge

Start with a professional operations representative for approved-document analysis, reconciliation preparation, reporting, research and draft preparation. Use synthetic data for engineering tests. Do not connect live employer/client data until tenant isolation, consent enforcement, retention, incident response and security review are complete.

## Deferred infrastructure

FastAPI, PostgreSQL with row-level security, OIDC/WebAuthn, policy decision point, secrets broker, malware scanning, observability, model gateway and durable workflow orchestration remain subsequent integration milestones. This v0.2 package intentionally keeps the core dependency-free so policy and provenance behavior can be tested independently of vendors.


## Human-in-the-Loop Visual Attestation

Visual Attestation is an evidence-review capability within the existing representative lifecycle, not a separate authority plane. It consumes model assessments and references to preserved visual evidence, applies risk/uncertainty/conflict routing, and creates a human attestation bound to exact evidence and model-output digests. High, critical and unknown risk require review regardless of model confidence; missing evidence or unavailable reviewer capacity results in HOLD.

Human verdicts include OBSERVED, NOT_OBSERVED, UNCERTAIN, EVIDENCE_UNUSABLE and DISAGREES_WITH_MODEL. The attestation records reviewer identity, time, rationale and whether the model output was revealed before the human's assessment. Human observations are evidence, not infallible truth. Corrections remain pending independent validation and are not automatically training labels.

This capability grants no authority or physical control. Existing consent, owner/organisation authority, capability and execution gateway remain authoritative. An operational stop requires a separately authorised control integration. The initial dependency-free module is a policy reference; media storage, reviewer authentication, durable API, calibrated uncertainty, queue orchestration and hardware integrations remain deferred.
