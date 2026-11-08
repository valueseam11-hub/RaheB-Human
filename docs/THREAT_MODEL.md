# Threat Model — Foundation v0.1

## Assets

Human identity and account access; owner-approved knowledge; employer/client information; authority contracts; consent records; capability evidence; approval events; credentials and tool permissions; audit evidence.

## Trust boundaries

- Human owner ↔ platform identity service
- Owner data ↔ employer/client data
- Model/provider ↔ RaheB control plane
- Retrieved content ↔ trusted policy/configuration
- AI representative ↔ external tools and side effects
- Service operator ↔ owner-controlled consent and authority

Treat documents, emails, retrieved pages, model outputs, tool metadata and external MCP servers as untrusted input. They must never override system policy or authority contracts.

## Principal threats and required controls

| Threat | Required control |
|---|---|
| Prompt injection in documents or email | Isolate untrusted content; no authority changes from retrieved text |
| Scope escalation | Allow-list task, tool and data scopes; deny by default |
| Stale/replayed approval | Bind approval to task digest, representative version, authority version, expiry and nonce |
| Revocation race | Re-check at side-effect boundary; cancel queued work; test concurrent revoke/execute |
| Credential theft | No raw long-lived credentials in model context; narrow brokered tools |
| Cross-tenant disclosure | Database row-level security plus application checks and isolation tests |
| False capability claim | Capability registry requires scoped, versioned test evidence |
| Human impersonation | AI disclosure and attributable action records |
| Log leakage | Redaction, least privilege, retention controls and secrets exclusion |
| Ledger tampering | Signed, durable, externally verifiable append-only evidence in production |

## Fail-safe rules

Unknown identity, consent, capability or authority state must not become permission. Hold or deny. Stop/revoke must be available independently of the model provider. Never represent a hash-chain check as proof of truth, correctness or authorization.

## Known v0.1 gaps

No authentication, persistent storage, cryptographic signing, key management, concurrency-safe revocation, rate limiting, production policy engine, data-loss prevention, malware scanning, tenant isolation or deployment controls are implemented here. These are release blockers for live customer data or real-world tool execution.
