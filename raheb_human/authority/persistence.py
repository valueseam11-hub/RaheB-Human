"""Durable SQLite authority records for RaheB Human's synthetic API.

The caller must derive owner_id from an authenticated server-side session.
SQLite is a single-node persistence adapter, not a distributed production
authority service. No function in this module executes external actions.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import uuid4


class AuthorityStoreError(ValueError):
    pass


class AuthorityHold(AuthorityStoreError):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("timezone-aware datetime required")
    return dt.astimezone(timezone.utc).isoformat()


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def init_authority_schema(con: sqlite3.Connection) -> None:
    con.executescript("""
    DROP TRIGGER IF EXISTS authority_events_no_delete;
    DROP TRIGGER IF EXISTS authority_warrants_no_delete;
    CREATE TABLE IF NOT EXISTS authority_warrants (
      warrant_id TEXT PRIMARY KEY,
      owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      representative_id TEXT NOT NULL REFERENCES representatives(id) ON DELETE CASCADE,
      representative_version INTEGER NOT NULL CHECK(representative_version > 0),
      authorizer_id TEXT NOT NULL,
      authority_source TEXT NOT NULL CHECK(authority_source IN ('INDIVIDUAL_OWNER','ORGANISATION')),
      organisation_id TEXT,
      purpose TEXT NOT NULL,
      actions_json TEXT NOT NULL,
      resources_json TEXT NOT NULL,
      limits_json TEXT NOT NULL,
      parent_warrant_id TEXT REFERENCES authority_warrants(warrant_id),
      issued_at TEXT NOT NULL,
      expires_at TEXT NOT NULL,
      warrant_digest TEXT NOT NULL CHECK(length(warrant_digest)=64),
      UNIQUE(owner_id,warrant_id)
    );
    CREATE INDEX IF NOT EXISTS idx_authority_warrants_owner ON authority_warrants(owner_id,issued_at);
    CREATE INDEX IF NOT EXISTS idx_authority_warrants_rep ON authority_warrants(owner_id,representative_id,expires_at);
    CREATE TABLE IF NOT EXISTS authority_revocations (
      revocation_id TEXT PRIMARY KEY,
      owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      warrant_id TEXT NOT NULL REFERENCES authority_warrants(warrant_id),
      revoked_by TEXT NOT NULL,
      reason TEXT NOT NULL,
      revoked_at TEXT NOT NULL,
      UNIQUE(owner_id,warrant_id)
    );
    CREATE TABLE IF NOT EXISTS authority_approvals (
      approval_id TEXT PRIMARY KEY,
      owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      warrant_id TEXT NOT NULL REFERENCES authority_warrants(warrant_id),
      representative_id TEXT NOT NULL,
      representative_version INTEGER NOT NULL,
      warrant_digest TEXT NOT NULL,
      task_id TEXT,
      action TEXT NOT NULL,
      resource TEXT NOT NULL,
      purpose TEXT NOT NULL,
      output_digest TEXT NOT NULL CHECK(length(output_digest)=64),
      request_digest TEXT NOT NULL CHECK(length(request_digest)=64),
      approved_by TEXT NOT NULL,
      approved_at TEXT NOT NULL,
      expires_at TEXT NOT NULL,
      consumed_at TEXT,
      UNIQUE(owner_id,approval_id)
    );
    CREATE INDEX IF NOT EXISTS idx_authority_approvals_owner ON authority_approvals(owner_id,approved_at);
    CREATE TABLE IF NOT EXISTS authority_budget_reservations (
      reservation_id TEXT PRIMARY KEY,
      owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      warrant_id TEXT NOT NULL REFERENCES authority_warrants(warrant_id),
      approval_id TEXT NOT NULL UNIQUE REFERENCES authority_approvals(approval_id),
      idempotency_key TEXT NOT NULL,
      money TEXT NOT NULL,
      tokens INTEGER NOT NULL CHECK(tokens >= 0),
      reserved_at TEXT NOT NULL,
      UNIQUE(owner_id,warrant_id,idempotency_key)
    );
    CREATE TABLE IF NOT EXISTS authority_events (
      sequence INTEGER PRIMARY KEY AUTOINCREMENT,
      event_id TEXT NOT NULL UNIQUE,
      owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      subject_id TEXT NOT NULL,
      event_type TEXT NOT NULL,
      payload_json TEXT NOT NULL,
      occurred_at TEXT NOT NULL,
      previous_digest TEXT NOT NULL,
      record_digest TEXT NOT NULL UNIQUE
    );
    CREATE INDEX IF NOT EXISTS idx_authority_events_owner_seq ON authority_events(owner_id,sequence);
    CREATE TRIGGER IF NOT EXISTS authority_events_no_update
      BEFORE UPDATE ON authority_events BEGIN
      SELECT RAISE(ABORT,'authority events are append-only');
    END;
    CREATE TRIGGER IF NOT EXISTS authority_warrants_no_update
      BEFORE UPDATE ON authority_warrants BEGIN
      SELECT RAISE(ABORT,'authority warrants are immutable; issue a new version');
    END;
    """)


def _event(con, owner_id: str, subject_id: str, event_type: str, payload: dict) -> None:
    row = con.execute(
        "SELECT record_digest FROM authority_events WHERE owner_id=? ORDER BY sequence DESC LIMIT 1",
        (owner_id,),
    ).fetchone()
    previous = row["record_digest"] if row else "GENESIS"
    occurred = iso(utcnow())
    body = {"owner_id": owner_id, "subject_id": subject_id, "event_type": event_type,
            "payload": payload, "occurred_at": occurred, "previous_digest": previous}
    record = sha256(canonical_json(body))
    con.execute("""INSERT INTO authority_events
      (event_id,owner_id,subject_id,event_type,payload_json,occurred_at,previous_digest,record_digest)
      VALUES(?,?,?,?,?,?,?,?)""",
      (str(uuid4()), owner_id, subject_id, event_type, canonical_json(payload),
       occurred, previous, record))


def verify_authority_events(con, owner_id: str) -> bool:
    previous = "GENESIS"
    rows = con.execute(
        "SELECT * FROM authority_events WHERE owner_id=? ORDER BY sequence", (owner_id,)
    ).fetchall()
    for row in rows:
        body = {"owner_id": row["owner_id"], "subject_id": row["subject_id"],
                "event_type": row["event_type"], "payload": json.loads(row["payload_json"]),
                "occurred_at": row["occurred_at"], "previous_digest": row["previous_digest"]}
        expected = sha256(canonical_json(body))
        if row["previous_digest"] != previous or expected != row["record_digest"]:
            return False
        previous = row["record_digest"]
    return True


def issue_warrant(con, *, owner_id: str, representative_id: str,
                  representative_version: int, authorizer_id: str,
                  authority_source: str, purpose: str, actions: list[str],
                  resources: list[str], limits: dict, expires_at: datetime,
                  organisation_id: str | None = None,
                  parent_warrant_id: str | None = None) -> dict:
    now = utcnow()
    if expires_at.tzinfo is None or expires_at <= now:
        raise AuthorityStoreError("warrant expiry must be in the future")
    if authority_source not in {"INDIVIDUAL_OWNER", "ORGANISATION"}:
        raise AuthorityStoreError("unsupported authority source")
    if authority_source == "ORGANISATION":
        raise AuthorityHold("organisation authority issuance is not enabled until organisation identity is verified")
    if not actions or not resources or not purpose.strip():
        raise AuthorityStoreError("purpose, actions and resources are required")
    rep = con.execute(
        "SELECT version FROM representatives WHERE id=? AND owner_id=?",
        (representative_id, owner_id),
    ).fetchone()
    if not rep or rep["version"] != representative_version:
        raise AuthorityHold("representative ownership or version mismatch")
    if parent_warrant_id:
        parent = _active_warrant(con, owner_id, parent_warrant_id, now)
        if parent["purpose"] != purpose:
            raise AuthorityHold("delegation cannot change purpose")
        if not set(actions).issubset(set(json.loads(parent["actions_json"]))):
            raise AuthorityHold("delegated actions exceed parent")
        if not set(resources).issubset(set(json.loads(parent["resources_json"]))):
            raise AuthorityHold("delegated resources exceed parent")
        if expires_at > datetime.fromisoformat(parent["expires_at"]):
            raise AuthorityHold("child warrant outlives parent")
        parent_limits = json.loads(parent["limits_json"])
        for key, child_value in limits.items():
            parent_value = parent_limits.get(key)
            if parent_value is None or child_value is None or Decimal(str(child_value)) > Decimal(str(parent_value)):
                raise AuthorityHold(f"delegated {key} limit exceeds parent or is unbounded")
    warrant_id = str(uuid4())
    body = {
        "warrant_id": warrant_id, "owner_id": owner_id,
        "representative_id": representative_id, "representative_version": representative_version,
        "authorizer_id": authorizer_id, "authority_source": authority_source,
        "purpose": purpose, "actions": sorted(set(actions)), "resources": sorted(set(resources)),
        "limits": limits, "parent_warrant_id": parent_warrant_id,
        "issued_at": iso(now), "expires_at": iso(expires_at),
    }
    warrant_digest = sha256(canonical_json(body))
    con.execute("""INSERT INTO authority_warrants
      (warrant_id,owner_id,representative_id,representative_version,authorizer_id,
       authority_source,organisation_id,purpose,actions_json,resources_json,limits_json,
       parent_warrant_id,issued_at,expires_at,warrant_digest)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (warrant_id, owner_id, representative_id, representative_version, authorizer_id,
       authority_source, organisation_id, purpose, canonical_json(body["actions"]),
       canonical_json(body["resources"]), canonical_json(limits), parent_warrant_id,
       body["issued_at"], body["expires_at"], warrant_digest))
    _event(con, owner_id, warrant_id, "WARRANT_ISSUED",
           {"warrant_digest": warrant_digest, "authority_source": authority_source,
            "representative_version": representative_version, "parent_warrant_id": parent_warrant_id})
    return {"warrant_id": warrant_id, "warrant_digest": warrant_digest,
            "issued_at": body["issued_at"], "expires_at": body["expires_at"]}


def _active_warrant(con, owner_id: str, warrant_id: str, now: datetime):
    current_id = warrant_id
    seen = set()
    leaf = None
    while current_id:
        if current_id in seen:
            raise AuthorityHold("delegation cycle detected")
        seen.add(current_id)
        row = con.execute(
            "SELECT * FROM authority_warrants WHERE warrant_id=? AND owner_id=?",
            (current_id, owner_id),
        ).fetchone()
        if not row:
            raise AuthorityHold("warrant or parent authority missing")
        if leaf is None:
            leaf = row
        if con.execute("SELECT 1 FROM authority_revocations WHERE owner_id=? AND warrant_id=?",
                       (owner_id, current_id)).fetchone():
            raise AuthorityHold("warrant or parent authority revoked")
        if now < datetime.fromisoformat(row["issued_at"]) or now >= datetime.fromisoformat(row["expires_at"]):
            raise AuthorityHold("warrant or parent authority expired or not yet valid")
        current_id = row["parent_warrant_id"]
    return leaf


def revoke_warrant(con, *, owner_id: str, warrant_id: str, revoked_by: str, reason: str) -> None:
    row = con.execute("SELECT 1 FROM authority_warrants WHERE warrant_id=? AND owner_id=?",
                      (warrant_id, owner_id)).fetchone()
    if not row:
        raise AuthorityHold("warrant not found")
    try:
        con.execute("""INSERT INTO authority_revocations
          (revocation_id,owner_id,warrant_id,revoked_by,reason,revoked_at)
          VALUES(?,?,?,?,?,?)""",
          (str(uuid4()), owner_id, warrant_id, revoked_by, reason.strip() or "owner withdrew authority", iso(utcnow())))
    except sqlite3.IntegrityError as exc:
        raise AuthorityHold("warrant already revoked") from exc
    _event(con, owner_id, warrant_id, "WARRANT_REVOKED", {"revoked_by": revoked_by, "reason": reason})


def approve_exact_action(con, *, owner_id: str, approved_by: str, warrant_id: str,
                         action: str, resource: str, purpose: str, output_digest: str,
                         task_id: str | None, expires_at: datetime) -> dict:
    now = utcnow()
    warrant = _active_warrant(con, owner_id, warrant_id, now)
    if expires_at.tzinfo is None or expires_at <= now or expires_at > datetime.fromisoformat(warrant["expires_at"]):
        raise AuthorityHold("approval expiry must be future and no later than warrant expiry")
    if action not in json.loads(warrant["actions_json"]) or resource not in json.loads(warrant["resources_json"]):
        raise AuthorityHold("action or resource outside warrant")
    if purpose != warrant["purpose"]:
        raise AuthorityHold("purpose mismatch")
    if len(output_digest) != 64 or any(c not in "0123456789abcdef" for c in output_digest.lower()):
        raise AuthorityStoreError("output_digest must be a SHA-256 hex digest")
    request = {
        "owner_id": owner_id, "warrant_id": warrant_id,
        "warrant_digest": warrant["warrant_digest"],
        "representative_id": warrant["representative_id"],
        "representative_version": warrant["representative_version"],
        "task_id": task_id, "action": action, "resource": resource,
        "purpose": purpose, "output_digest": output_digest.lower(),
    }
    request_digest = sha256(canonical_json(request))
    approval_id = str(uuid4())
    con.execute("""INSERT INTO authority_approvals
      (approval_id,owner_id,warrant_id,representative_id,representative_version,warrant_digest,
       task_id,action,resource,purpose,output_digest,request_digest,approved_by,approved_at,expires_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (approval_id, owner_id, warrant_id, warrant["representative_id"],
       warrant["representative_version"], warrant["warrant_digest"], task_id, action,
       resource, purpose, output_digest.lower(), request_digest, approved_by,
       iso(now), iso(expires_at)))
    _event(con, owner_id, approval_id, "ACTION_APPROVED",
           {"warrant_id": warrant_id, "request_digest": request_digest,
            "output_digest": output_digest.lower(), "approved_by": approved_by})
    return {"approval_id": approval_id, "request_digest": request_digest,
            "approved_at": iso(now), "expires_at": iso(expires_at)}


def admit_once(con, *, owner_id: str, approval_id: str, idempotency_key: str,
               action: str, resource: str, purpose: str, output_digest: str,
               estimated_money: str, estimated_tokens: int, retry_number: int = 0,
               active_agent_count: int = 1, elapsed_seconds: int = 0) -> dict:
    # Acquire SQLite's write lock before checking and consuming the approval.
    con.execute("BEGIN IMMEDIATE")
    approval = con.execute(
        "SELECT * FROM authority_approvals WHERE approval_id=? AND owner_id=?",
        (approval_id, owner_id),
    ).fetchone()
    if not approval:
        raise AuthorityHold("approval missing")
    now = utcnow()
    if approval["consumed_at"]:
        raise AuthorityHold("approval already consumed")
    if now >= datetime.fromisoformat(approval["expires_at"]):
        raise AuthorityHold("approval expired")
    warrant = _active_warrant(con, owner_id, approval["warrant_id"], now)
    rep = con.execute("SELECT version FROM representatives WHERE id=? AND owner_id=?",
                      (approval["representative_id"], owner_id)).fetchone()
    if not rep or rep["version"] != approval["representative_version"]:
        raise AuthorityHold("representative version changed")
    if (action, resource, purpose, output_digest.lower()) != (
        approval["action"], approval["resource"], approval["purpose"], approval["output_digest"]
    ):
        raise AuthorityHold("approved action or output has changed")
    request = {
        "owner_id": owner_id, "warrant_id": approval["warrant_id"],
        "warrant_digest": warrant["warrant_digest"],
        "representative_id": approval["representative_id"],
        "representative_version": approval["representative_version"],
        "task_id": approval["task_id"], "action": action, "resource": resource,
        "purpose": purpose, "output_digest": output_digest.lower(),
    }
    if sha256(canonical_json(request)) != approval["request_digest"]:
        raise AuthorityHold("approval binding integrity check failed")
    limits = json.loads(warrant["limits_json"])
    money = Decimal(estimated_money)
    tokens = int(estimated_tokens)
    if money < 0 or tokens < 0:
        raise AuthorityStoreError("resource estimates cannot be negative")
    money_limit = limits.get("money")
    token_limit = limits.get("tokens")
    if limits.get("retries") is None or retry_number < 0 or retry_number > int(limits["retries"]):
        raise AuthorityHold("retry ceiling missing or exceeded")
    if limits.get("agent_count") is None or active_agent_count < 1 or active_agent_count > int(limits["agent_count"]):
        raise AuthorityHold("agent-count ceiling missing or exceeded")
    if limits.get("duration_seconds") is None or elapsed_seconds < 0 or elapsed_seconds > int(limits["duration_seconds"]):
        raise AuthorityHold("duration ceiling missing or exceeded")
    if money_limit is None or token_limit is None:
        raise AuthorityHold("money and token ceilings must both be explicit")
    if money > Decimal(str(money_limit)) or tokens > int(token_limit):
        raise AuthorityHold("single-action consequence estimate exceeds warrant ceiling")
    prior = con.execute("""SELECT money,tokens FROM authority_budget_reservations
      WHERE owner_id=? AND warrant_id=?""", (owner_id, approval["warrant_id"])).fetchall()
    used_money = sum((Decimal(row["money"]) for row in prior), Decimal("0"))
    used_tokens = sum(int(row["tokens"]) for row in prior)
    if used_money + money > Decimal(str(money_limit)) or used_tokens + tokens > int(token_limit):
        raise AuthorityHold("cumulative consequence budget exhausted")
    con.execute("""INSERT INTO authority_budget_reservations
      (reservation_id,owner_id,warrant_id,approval_id,idempotency_key,money,tokens,reserved_at)
      VALUES(?,?,?,?,?,?,?,?)""",
      (str(uuid4()), owner_id, approval["warrant_id"], approval_id,
       idempotency_key, str(money), tokens, iso(now)))
    consumed = con.execute("UPDATE authority_approvals SET consumed_at=? WHERE approval_id=? AND consumed_at IS NULL",
                           (iso(now), approval_id))
    if consumed.rowcount != 1:
        raise AuthorityHold("approval could not be consumed")
    _event(con, owner_id, approval_id, "ADMISSION_RESERVED",
           {"warrant_id": approval["warrant_id"], "idempotency_key": idempotency_key,
            "money": str(money), "tokens": tokens, "side_effect_permitted": False})
    return {"admitted": True, "approval_consumed": True, "money_reserved": str(money),
            "tokens_reserved": tokens, "side_effect_permitted": False,
            "notice": "Admission recorded only. No external action was executed."}
