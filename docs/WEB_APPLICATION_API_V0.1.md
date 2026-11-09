# RaheB Human Web Application & API v0.1

## Implemented
- Responsive public site and interactive synthetic workspace.
- FastAPI API, SQLite development store, password hashing primitive, opaque HTTP-only session cookie, owner-scoped representative records and hash-linked evidence events.
- Health/public configuration/legal status, login/logout/me, representative listing/creation, knowledge/task/evidence routes.
- Dockerfile and Docker Compose.

## Safety gates
- Account registration disabled until approved service agreement and privacy notice are supplied.
- Personal knowledge ingestion disabled until legal documents and separate persistent-memory consent are live.
- Representatives remain DRAFT. No authority or model access.
- Task admission and execution disabled. No external actions.
- Browser demo uses synthetic deterministic examples only.

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
This is a development foundation, not a production service. Before public accounts or personal data: approved legal documents; CSRF/origin checks; rate limiting; email verification and password reset; MFA/passkeys; secret management; secure cookies; encrypted PostgreSQL with tenant RLS; backup/restore; retention/deletion; signed audit anchoring; CSP/security headers; pinned dependencies and vulnerability scanning; monitoring/incident response; upload quarantine/malware scanning; privacy workflows and threat-model review.

SQLite is not encrypted at rest. Hash chaining is not a digital signature, independent witness or proof of truth. The API does not call an LLM, execute tools or perform real-world actions.
