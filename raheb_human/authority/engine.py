"""RaheB Human deterministic authority policy primitives.

Reference policy core only: not authentication, durable storage, a payment
control, or a production execution gateway. External actions remain disabled.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from threading import RLock
from typing import Iterable
from uuid import uuid4


class Decision(str, Enum):
    PERMIT = "PERMIT"
    HOLD = "HOLD"
    DENY = "DENY"


class AuthorityError(ValueError):
    pass


@dataclass(frozen=True)
class ConsequenceLimits:
    money: Decimal | None = None
    tokens: int | None = None
    retries: int | None = None
    agent_count: int | None = None
    duration_seconds: int | None = None

    def __post_init__(self):
        if self.money is not None and self.money < 0:
            raise ValueError("money limit cannot be negative")
        for name in ("tokens", "retries", "agent_count", "duration_seconds"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} limit cannot be negative")


@dataclass(frozen=True)
class AuthorityWarrant:
    warrant_id: str
    owner_id: str
    representative_id: str
    representative_version: int
    authorizer_id: str
    authority_source: str
    purpose: str
    allowed_actions: frozenset[str]
    allowed_resources: frozenset[str]
    expires_at: datetime
    limits: ConsequenceLimits = field(default_factory=ConsequenceLimits)
    approval_required: bool = True
    parent_warrant_id: str | None = None
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not all((self.warrant_id, self.owner_id, self.representative_id,
                    self.authorizer_id, self.authority_source, self.purpose)):
            raise ValueError("warrant identity, authority source and purpose are required")
        if self.representative_version < 1:
            raise ValueError("representative_version must be positive")
        if self.expires_at.tzinfo is None or self.issued_at.tzinfo is None:
            raise ValueError("warrant timestamps must be timezone-aware")
        if not self.allowed_actions or not self.allowed_resources:
            raise ValueError("warrant must name at least one action and resource")
        if self.expires_at <= self.issued_at:
            raise ValueError("warrant expiry must follow issue time")

    @classmethod
    def issue(cls, **kwargs):
        return cls(warrant_id=str(uuid4()), **kwargs)


@dataclass(frozen=True)
class ActionRequest:
    owner_id: str
    representative_id: str
    representative_version: int
    action: str
    resource: str
    purpose: str
    idempotency_key: str
    estimated_money: Decimal = Decimal("0")
    estimated_tokens: int = 0
    retry_number: int = 0
    active_agent_count: int = 1
    elapsed_seconds: int = 0
    human_approval_id: str | None = None


@dataclass(frozen=True)
class Admission:
    decision: Decision
    reason: str
    warrant_id: str | None = None


class RevocationRegistry:
    """In-memory reference; production requires durable, shared revocation state."""
    def __init__(self):
        self._revoked = {}
        self._lock = RLock()

    def revoke(self, warrant_id: str, reason: str):
        with self._lock:
            self._revoked[warrant_id] = reason or "authority withdrawn"

    def reason(self, warrant_id: str):
        with self._lock:
            return self._revoked.get(warrant_id)


class ConsequenceBudget:
    """Atomic in-process reservations; not a distributed budget ledger."""
    def __init__(self, limits: ConsequenceLimits):
        self.limits = limits
        self._reserved = {}
        self._lock = RLock()

    def reserve(self, key: str, money: Decimal, tokens: int) -> bool:
        if not key or money < 0 or tokens < 0:
            return False
        with self._lock:
            if key in self._reserved:
                return self._reserved[key] == (money, tokens)
            used_money = sum((v[0] for v in self._reserved.values()), Decimal("0"))
            used_tokens = sum(v[1] for v in self._reserved.values())
            if self.limits.money is None or used_money + money > self.limits.money:
                return False
            if self.limits.tokens is None or used_tokens + tokens > self.limits.tokens:
                return False
            self._reserved[key] = (money, tokens)
            return True

    def release(self, key: str):
        with self._lock:
            self._reserved.pop(key, None)

    def totals(self):
        with self._lock:
            return (sum((v[0] for v in self._reserved.values()), Decimal("0")),
                    sum(v[1] for v in self._reserved.values()))


class AuthorityEnforcement:
    """Checks exact, current, attenuated authority before admission."""
    def __init__(self, warrants: Iterable[AuthorityWarrant],
                 revocations: RevocationRegistry | None = None):
        self.warrants = {w.warrant_id: w for w in warrants}
        self.revocations = revocations or RevocationRegistry()
        self.budgets = {w.warrant_id: ConsequenceBudget(w.limits) for w in warrants}

    def _revocation_reason(self, warrant):
        current = warrant
        seen = set()
        while current:
            if current.warrant_id in seen:
                return "delegation cycle detected"
            seen.add(current.warrant_id)
            reason = self.revocations.reason(current.warrant_id)
            if reason:
                return f"authority revoked: {reason}"
            if not current.parent_warrant_id:
                break
            current = self.warrants.get(current.parent_warrant_id)
            if current is None:
                return "parent authority missing"
        return None

    def admit(self, warrant_id: str, request: ActionRequest,
              now: datetime | None = None) -> Admission:
        warrant = self.warrants.get(warrant_id)
        if warrant is None:
            return Admission(Decision.HOLD, "warrant missing or unknown")
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            return Admission(Decision.HOLD, "current time is not timezone-aware", warrant_id)
        revoked = self._revocation_reason(warrant)
        if revoked:
            return Admission(Decision.HOLD, revoked, warrant_id)
        if now < warrant.issued_at or now >= warrant.expires_at:
            return Admission(Decision.HOLD, "warrant not currently valid", warrant_id)
        if (request.owner_id != warrant.owner_id or
            request.representative_id != warrant.representative_id or
            request.representative_version != warrant.representative_version):
            return Admission(Decision.HOLD, "owner, representative or version mismatch", warrant_id)
        if request.purpose != warrant.purpose:
            return Admission(Decision.DENY, "purpose is outside the warrant", warrant_id)
        if request.action not in warrant.allowed_actions or request.resource not in warrant.allowed_resources:
            return Admission(Decision.DENY, "action or resource is outside the warrant", warrant_id)
        if warrant.approval_required and not request.human_approval_id:
            return Admission(Decision.HOLD, "specific human approval is required", warrant_id)
        limits = warrant.limits
        if limits.retries is None or request.retry_number > limits.retries:
            return Admission(Decision.HOLD, "retry ceiling missing or exceeded", warrant_id)
        if limits.agent_count is None or request.active_agent_count > limits.agent_count:
            return Admission(Decision.HOLD, "agent-count ceiling missing or exceeded", warrant_id)
        if limits.duration_seconds is None or request.elapsed_seconds > limits.duration_seconds:
            return Admission(Decision.HOLD, "duration ceiling missing or exceeded", warrant_id)
        if not self.budgets[warrant_id].reserve(request.idempotency_key,
                                                 request.estimated_money,
                                                 request.estimated_tokens):
            return Admission(Decision.HOLD, "consequence budget missing, exhausted or reservation conflict", warrant_id)
        return Admission(Decision.PERMIT, "within warrant; reservation recorded", warrant_id)


def delegate(parent: AuthorityWarrant, *, child_authorizer_id: str,
             purpose: str, actions: Iterable[str], resources: Iterable[str],
             expires_at: datetime, limits: ConsequenceLimits,
             approval_required: bool = True) -> AuthorityWarrant:
    """Issue a strictly attenuated child warrant; never widen parent authority."""
    child_actions, child_resources = frozenset(actions), frozenset(resources)
    if not child_actions or not child_actions.issubset(parent.allowed_actions):
        raise AuthorityError("child actions must be a non-empty subset of parent actions")
    if not child_resources or not child_resources.issubset(parent.allowed_resources):
        raise AuthorityError("child resources must be a non-empty subset of parent resources")
    if purpose != parent.purpose:
        raise AuthorityError("delegation cannot change the authorised purpose")
    if expires_at > parent.expires_at:
        raise AuthorityError("child expiry cannot exceed parent expiry")
    for name in ("money", "tokens", "retries", "agent_count", "duration_seconds"):
        p, c = getattr(parent.limits, name), getattr(limits, name)
        if p is None and c is not None:
            raise AuthorityError(f"child cannot create a {name} allowance")
        if p is not None and (c is None or c > p):
            raise AuthorityError(f"child {name} limit must not exceed parent")
    return AuthorityWarrant.issue(
        owner_id=parent.owner_id, representative_id=parent.representative_id,
        representative_version=parent.representative_version,
        authorizer_id=child_authorizer_id, authority_source="delegated",
        purpose=purpose, allowed_actions=child_actions,
        allowed_resources=child_resources, expires_at=expires_at,
        limits=limits, approval_required=approval_required,
        parent_warrant_id=parent.warrant_id)
