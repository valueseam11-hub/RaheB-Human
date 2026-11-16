# Production tenant-isolated persistence — v0.1

## Scope

This branch creates the first PostgreSQL persistence boundary for RaheB Human. It is a production-foundation milestone, not a production launch. It is deliberately separate from the current SQLite FastAPI demo and does not enable user registration, personal data ingestion, model invocation or external actions.

## Included

- PostgreSQL 16 schema for owner accounts, representatives, authority contracts, purpose-specific consent, capability assessments, provenance-only knowledge document references, tasks, exact human approvals and evidence events.
- ENABLE ROW LEVEL SECURITY and FORCE ROW LEVEL SECURITY on every tenant-owned table.
- A transaction-local raheb.owner_id policy. Missing tenant context yields no visible tenant rows.
- Composite owner/resource foreign keys to prevent cross-owner references.
- Database trigger preventing evidence event updates and deletes.
- PostgreSQL tenant transaction adapter that validates an authenticated UUID and binds it transaction-locally.
- Migration runner requiring a separate migration DSN.
- CI PostgreSQL service and integration tests for cross-tenant read/write isolation and evidence immutability.

## Critical integration boundary

The current FastAPI routes still use the SQLite demo schema. The new raheb_* PostgreSQL schema is not yet the live application database, and the current users.id/representatives.owner_id identifiers have not been migrated to UUID owner identities. Do not set the production web service to this database or point the existing SQLite adapter at it.

The next integration milestone must:
1. Establish a verified identity/session mapping to immutable owner UUIDs.
2. Keep authentication/session lookup separate from tenant data access, with a tightly scoped auth lookup mechanism.
3. Convert every owner-scoped route to PostgresTenantStore.tenant_transaction(authenticated_owner_uuid).
4. Port authority warrants, approvals, revocations, budget reservations and event writes to PostgreSQL with row locking and atomic transactions.
5. Define organisation membership/admin roles and the second authority key before workplace deployment.
6. Add object-storage quarantine, malware scanning, retention and deletion/cryptographic-erasure lifecycle.
7. Prove that the runtime DB role is not a superuser, table owner or BYPASSRLS role.

## Privacy and evidence

The append-only evidence trigger is an integrity control, not an excuse to retain personal data indefinitely. A separate retention and erasure design is required. Event payloads must be minimized and must not contain source documents, secrets, credentials or unnecessary personal data. Account closure and lawful deletion need a reviewed process for dependent data, backups, legal holds and any retained non-identifying integrity anchors.

## Validation

CI starts a disposable PostgreSQL 16 service, applies only 0001_tenant_runtime.sql, and runs integration tests. Passing these tests validates the schema's tested RLS behavior; it does not validate the live website, authentication mapping, production credentials, backup/restore, operational monitoring or external execution controls.

## Rollout gate

Do not merge into main, deploy, accept real user data or enable external actions until the PostgreSQL route integration and identity/security tests pass, the database roles are separated, and independent security review is complete.
