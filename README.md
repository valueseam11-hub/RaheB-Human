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

### Work redistribution and professional growth
The workforce layer also measures where human effort moves after AI is introduced: review, correction, exceptions and coordination are counted alongside AI-assisted preparation. It preserves negative time savings and quality regressions. Learning primitives support explanation, guided practice and human performance checks; AI cannot attest to a person's competence. The platform explicitly excludes employee replaceability scoring and employment decisions. See the workforce trust document for limitations and data boundaries.


## Work Identity & Recognition Intelligence v0.1

The new owner-controlled work identity layer records the difference between formal role expectations and actual work performed as AI changes workflows. It captures observation periods, frequency, AI assistance, retained human responsibility, evidence status and optional baseline/observed outcome measures. It prepares neutral recognition summaries for discussion about role scope, workload, skills, business outcomes, compensation review or title/level review.

Evidence levels remain distinct (self-reported, documented, corroborated, disputed and not verified). Potential role-scope gaps are review prompts, not proof of contractual change. No pay, promotion, job-security or legal outcome is predicted. Disclosure requires explicit owner approval and selected entries. No employee monitoring, ranking or replaceability scoring is supported.

Run its tests with:

    python -m unittest discover -s tests -p 'test_work_identity.py' -v

This v0.1 layer is in-memory scaffolding only; it is not connected to persistent storage, the web API, employer systems or compensation benchmarking. Use synthetic data only. See `docs/WORK_IDENTITY_AND_RECOGNITION_V0.1.md`.


## Career Transition & Human Interaction Boundaries v0.1

The workforce foundation now includes owner-directed career transition planning. It maps an owner-defined goal to dated, sourced skill requirements, attributable evidence and human development actions. Missing evidence is labelled NOT_YET_EVIDENCED, not lack of ability; disputed evidence is preserved. The layer does not predict layoffs, employability, salary or hiring outcomes.

Owners can mark professional communication and relationship work as HUMAN_OWNED, AI_PREPARE_ONLY or AI_ASSISTED_WITH_APPROVAL. AI-assisted interaction requires purpose-bound, expiring approval; existing task risk and authority controls still apply.

Run its tests with:

    python -m unittest discover -s tests -p 'test_career_transition.py' -v

This is deterministic in-memory scaffolding only. No live labour-market feed, role matching, persistent storage, API, résumé generation or employer integration is implemented. See `docs/CAREER_TRANSITION_AND_HUMAN_BOUNDARIES_V0.1.md`.


## Human Transition & Resilience Support v0.1

A private, person-directed check-in lets an owner record concerns about professional identity, career direction, financial uncertainty, skill confidence, workload, belonging and trust; choose the support they want; and prepare practical next steps. An organisational communication record separates confirmed facts from unknowns and names an accountable contact and next update.

This is deliberately non-clinical: no AI-grief diagnosis, grief-stage assignment, mental-health inference, resilience score or fitness-for-work score. Check-ins are private by default. Employer sharing requires explicit owner approval. The layer must never be used for performance management, redundancy selection, worker ranking or employability scoring.

Run its tests with:

    python -m unittest discover -s tests -p 'test_transition_support.py' -v

In-memory scaffolding only; no counselling, sentiment analysis, persistent storage, API, employer dashboard or emergency-support integration. Not production-ready. See `docs/HUMAN_TRANSITION_AND_RESILIENCE_SUPPORT_V0.1.md`.

## Career Intelligence Workspace v0.1

The synthetic workspace at `/app` now includes a local-only career evidence mapper. A person can enter a current role, a career direction, their own professional narrative, sourced role requirements and evidence they can substantiate. The browser pairs requirements and evidence by their displayed order and labels unmatched requirements `NOT YET EVIDENCED`; it does not infer a skills deficit or generate a candidate score.

The panel also provides questions to ask employers about AI-use rules, assessment methods, human review, candidate data and accommodations. Inputs in this career panel are processed only in the browser: they are not posted to the API, persisted, or shared with employers. This is an interaction prototype, not a live job-search engine, résumé generator, verified portfolio, or hiring predictor. Do not enter sensitive personal, employer or client information in the synthetic preview.
