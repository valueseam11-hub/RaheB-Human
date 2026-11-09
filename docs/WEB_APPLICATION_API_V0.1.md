# RaheB Human Web Application & API v0.1

## Implemented
- Responsive public website and interactive workspace at /app.
- FastAPI API and SQLite development persistence.
- Short-lived synthetic-only guest sessions; no public account registration.
- Owner-scoped representative records, synthetic knowledge fixtures, owner approval, deterministic task drafts, human review/rejection and hash-linked evidence events.
- API health/config/legal status, demo session lifecycle, login/logout/me, representatives, knowledge, tasks and evidence.
- Dockerfile and Docker Compose.

## Safety gates
- Account registration remains disabled until the approved service agreement and privacy notice are supplied.
- Real personal/employer/client knowledge ingestion remains disabled. The interactive app only offers fixed server-side synthetic fixtures.
- Representatives are DRAFT; no authority or model runtime is enabled.
- Draft creation is deterministic, uses synthetic fixtures only and invokes no AI model.
- Human draft approval does not trigger an external action.
- Guest demo data is tied to a short-lived synthetic user and removed when the demo session is ended.

## Run locally
Python 3.11+:
    python -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.txt
    uvicorn raheb_human.api.app:app --reload

Open http://127.0.0.1:8000 and /app. API docs: /api/docs.

Docker:
    docker compose up --build

Set a strong RAHEB_SESSION_PEPPER and RAHEB_COOKIE_SECURE=1 behind HTTPS before deployment.

## Production gaps
This is an application foundation, not a production service. Before public accounts or personal data: approved legal documents; email verification/password reset; MFA/passkeys; robust rate limiting; CSRF/origin policy review; secret management; secure cookie configuration; encrypted PostgreSQL with tenant RLS; backup/restore; retention/deletion; signed audit anchoring; CSP/security headers; pinned dependencies and vulnerability scanning; monitoring/incident response; upload quarantine/malware scanning; privacy workflows and independent threat-model review.

SQLite is not encrypted at rest. Hash chaining is not a digital signature, independent witness or proof of truth. The API does not call an LLM, execute tools or perform real-world actions.
