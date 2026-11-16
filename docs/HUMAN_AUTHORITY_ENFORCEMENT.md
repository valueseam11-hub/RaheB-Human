# Human Authority Enforcement — RaheB Human v0.1

## Governing rule

**Delegated capability is not sovereign authority.** A representative or child agent may act only within a current, specific authority warrant. Delegation may narrow authority; it may never enlarge it.

## Components

1. **Authority Origination** — only an identified owner or organisation authority source may originate a warrant. The model cannot create authority.
2. **Specific Authority Warrant** — binds owner, representative and version, authorizer, purpose, exact actions/resources, expiry, approval requirement and consequence ceilings.
3. **Delegation Attenuation** — child actions/resources are subsets; purpose is unchanged; expiry and every resource ceiling cannot exceed the parent.
4. **Revocation Propagation** — revoking a parent makes dependent child warrants non-admissible. Queued jobs, credentials, in-flight work and external commitments require integration adapters and reconciliation.
5. **Consequence Budgets** — money and tokens are separately reserved; retries, child-agent count and duration have hard ceilings. The model cannot increase a ceiling.
6. **Execution Admission** — exact authority is checked before a side effect. Missing, stale, mismatched, revoked or uncertain authority returns HOLD.
7. **Accountability** — production actions must record the human authorizer, warrant/version, representative/version, delegated agents, action, resource, reservation, approval, result and stop/revocation events.

## Admission sequence

IDENTITY → WARRANT → DELEGATION → REVOCATION → SCOPE → APPROVAL → BUDGET RESERVATION → ADMISSION

A PERMIT from this reference core is a policy decision only. It is not permission to call an external service yet. Production integrations must revalidate at the actual side-effect boundary and use idempotency keys.

## Irreversible action protocol

PREPARE → VALIDATE → PRESENT EXACT CONSEQUENCE → HUMAN APPROVES → REVALIDATE → EXECUTE ONCE → RECORD

Approval must bind to the exact action/output, resource, warrant, representative version, expiry and single-use idempotency key. A changed output, expired approval or revoked warrant returns HOLD. Completed external actions cannot be retroactively undone; adapters must report and reconcile their state.

## Two-key workplace authority

Workplace actions require both:
- **Owner authority:** the professional authorizes their representative and its task/purpose.
- **Organisation authority:** the organisation authorizes its own systems, data, tools and workflow.

Neither key can grant the other party's authority. Affected-party privacy, consent and legal rights remain constraints; neither key can waive another person's rights.

## Current implementation status and limitations

v0.1 adds a pure-Python policy core only. Revocations and budgets are in-memory, not durable or distributed. It does not authenticate authorizers, cryptographically sign warrants, persist approvals, implement organisation key issuance, bind approval to output digests, cancel external jobs, revoke provider credentials, execute tools, or provide payment/token gateway controls. It is not production-ready and must not process live personal, employer or client data. Existing app behavior remains synthetic-only and external actions remain disabled.
