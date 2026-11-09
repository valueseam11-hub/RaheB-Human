# RaheB Human

**Own an AI that represents you and your profession. It works for you. You remain in control.**

RaheB Human is building human-owned professional AI representatives. A representative can prepare, analyse, research and assist under a human owner's identity, approved knowledge, explicit authority and continuing oversight. It must disclose that it is AI and must never imply that the human personally performed work they did not perform.

## Architecture foundation v0.1

The dependency-free Python core establishes distinct owner and representative identities, versioned authority contracts, purpose-specific consent, scoped AI capability evidence, a fail-closed admission gateway and a hash-linked evidence ledger.

## Personal Representative Control Plane v0.1

HRCP coordinates the representative lifecycle:

- Register a representative against a verified owner identity and approved knowledge references.
- Require visible AI disclosure.
- Activate only with current service-processing consent and a matching, current authority contract.
- Pause or revoke the representative, cancel registered pending work and invalidate outstanding approvals.
- Require scoped capability evidence, current consent and a matching representative version before admission.
- Bind high-impact approvals to the exact task digest, owner, representative version, authority version and expiry; consume each approval once.
- Record lifecycle and admission evidence.

A successful admission is **not execution**. The reference implementation always returns `side_effect_permitted=False`; no external tool is invoked.

## Quick start

Requires Python 3.11+; no third-party runtime dependencies.

    python -m unittest discover -s tests -v

## Current scope and limitations

This is a testable architecture reference, not a production agent platform. HRCP is in-memory and process-local. It does not provide authentication, durable state, distributed revocation, secure timestamps, cryptographic signatures, tenant isolation, a model runtime, an API, or external tool execution. Caller-supplied owner IDs are not authentication. Do not use this implementation with live customer data or to authorize real-world side effects.

See:
- docs/ARCHITECTURE_FOUNDATION.md
- docs/THREAT_MODEL.md
- docs/PERSONAL_REPRESENTATIVE_CONTROL_PLANE.md


## Personal Intelligence & Knowledge Engine v0.1

The owner-scoped knowledge reference store adds source metadata, per-source versioning, content digests, explicit owner approval, withdrawal and scope-filtered lexical retrieval. Submission and retrieval require both service-processing consent and separate persistent-memory consent. New source versions remain pending until approved. Retrieval returns source citations and treats content as untrusted input.

The reference implementation is in-memory and accepts caller-provided text only. It does not parse uploads, scan malware, authenticate owners, persist data, encrypt content or provide production tenant isolation. It must not be used with live customer, employer or client data.


## Website and application API v0.1

The public website is served by the FastAPI application. The interactive workspace is available at `/app`. Run locally with:

    pip install -r requirements.txt
    uvicorn raheb_human.api.app:app --reload

The workspace opens a short-lived, synthetic-only guest session. It supports a persisted representative draft, fixed synthetic knowledge fixtures, owner approval, deterministic task drafts, human review/rejection and a hash-linked evidence trail. It does not call an AI model or execute external actions.

Public account registration and personal/employer/client knowledge ingestion are deliberately disabled until approved legal documents, purpose-specific consent controls and production security safeguards are completed. See `docs/WEB_APPLICATION_API_V0.1.md`.


## Workforce Intelligence & Trust Foundation v0.1

The workforce module adds a conservative task assessment and evidence-first supervised workbench:

- Classifies routine, research, judgment, high-impact, human-interaction and unknown tasks.
- Uses SUPERVISED_EXECUTION, PREPARE_ONLY, HUMAN_OWNED or HOLD; missing approved data scope forces HOLD.
- Requires scoped evidence references before draft preparation; drafts never execute or send work.
- Provides exact task/output/owner/representative/authority approval-binding validation with expiry and nonce checks. Durable atomic nonce consumption is not implemented.
- Separates employee-owned personal scopes from employer-controlled system scopes.
- Calculates net time saved after AI preparation, human review and rework; negative savings remain visible.

Run the new policy tests with:

    python -m unittest discover -s tests -p 'test_work_intelligence.py' -v

This is deterministic policy scaffolding, not a validated occupational risk model or production authorization service. The module is not yet integrated with the web API, persistent task storage, model runtime or workplace connectors. Continue using synthetic demo data only. See `docs/WORKFORCE_INTELLIGENCE_AND_TRUST_V0.1.md`.
