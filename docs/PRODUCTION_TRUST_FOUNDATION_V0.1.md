# Production Trust Foundation v0.1

## Added
- PostgreSQL schema for owners, representatives, versioned authority contracts, purpose-specific consent, scoped capability assessments, provenance-bearing knowledge references, tasks, human approvals and evidence events.
- Row-level security and FORCE ROW LEVEL SECURITY on every owner-scoped table.
- Transaction-local tenant binding in the PostgreSQL adapter.
- Database-level append-only protection for evidence events.
- Optional integration tests for tenant isolation, cross-tenant insert rejection and evidence mutation rejection.
- Existing deterministic core includes authority, capability, consent, control-plane lifecycle, owner-reviewed knowledge and evidence ledger.

## Runtime invariants
1. Authenticate the person before resolving their immutable owner UUID.
2. Never accept owner identity from request JSON.
3. Runtime DB role must be non-superuser, non-owner and have no BYPASSRLS.
4. Bind tenant context inside every transaction with transaction-local set_config. Never use a session-global tenant setting with pooled connections.
5. Migrations use a separate migration role. Runtime role gets only necessary table privileges.
6. Do not grant runtime role table ownership, superuser or BYPASSRLS.
7. Documents belong in private object storage with scoped URLs, quarantine and verified content digests; database stores references and provenance.
8. Service consent does not imply memory, analytics, model training or employer sharing.
9. Evidence hashes provide tamper evidence, not proof of truth. Signing and independent anchoring remain separate work.
10. The FastAPI website still uses SQLite demo persistence. This adapter is not yet wired into HTTP endpoints. Do not process live personal or employer/client data.

## Apply and test
Apply migrations/postgresql/0001_trust_foundation.sql with a migration administrator. Set RAHEB_DATABASE_URL for a non-superuser runtime role. For tests, set RAHEB_TEST_DATABASE_URL to a disposable PostgreSQL database and run the Postgres integration test. It creates/drops a test role; never point it at production.
