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
