# RaheB Human

**Own an AI that represents you and your profession. It works for you. You remain in control.**

RaheB Human is building human-owned professional AI representatives. A representative can prepare, analyse, research and assist under a human owner's identity, approved knowledge, explicit authority and continuing oversight. It must disclose that it is AI and must never imply that the human personally performed work they did not perform.

## Foundation v0.1

This first architecture foundation establishes a small, dependency-free Python control core:

- **Identity boundary:** owner identity, representative identity and AI capability are distinct.
- **Authority contract:** every proposed tool action is checked against a versioned, time-bounded, revocable delegation.
- **Consent ledger:** consent is granular by purpose; optional purposes do not inherit from service consent.
- **Capability evidence:** human qualifications do not automatically become AI capabilities; capability claims require scoped test evidence.
- **Fail-closed gateway:** missing, expired, revoked or insufficient authority produces HOLD/DENY and no side effect.
- **Evidence chain:** append-only hash-linked records support tamper-evidence. Hash integrity does not prove truth, correctness or current authorization.

## Quick start

Requires Python 3.11+; no third-party runtime dependencies.

    python -m unittest discover -s tests -v

## Current scope and limitations

This is an architecture foundation, not a production agent platform. It does not yet provide authentication, persistent database storage, cryptographic signatures, key management, multi-tenant isolation, model orchestration, integrations, legal consent documents or a deployed service. The in-memory ledger is a testable reference implementation only. Do not use it to authorize real-world actions.

See docs/ARCHITECTURE_FOUNDATION.md and docs/THREAT_MODEL.md.
