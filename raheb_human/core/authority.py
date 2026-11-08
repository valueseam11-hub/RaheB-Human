"""Explicit, revocable authority contracts and deterministic admission checks."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class AuthorityDecision(StrEnum):
    ALLOW = "ALLOW"
    CONDITIONAL = "CONDITIONAL"
    HOLD = "HOLD"
    DENY = "DENY"


@dataclass(frozen=True)
class TaskRequest:
    task_type: str
    tool: str
    data_scopes: frozenset[str] = frozenset()
    high_impact: bool = False
    irreversible: bool = False
    human_approval_present: bool = False


@dataclass(frozen=True)
class AuthorityContract:
    contract_id: str
    owner_id: str
    representative_id: str
    version: int
    allowed_tasks: frozenset[str]
    allowed_tools: frozenset[str]
    data_scopes: frozenset[str]
    expires_at: datetime
    revoked: bool = False
    require_approval_for_high_impact: bool = True
    require_approval_for_irreversible: bool = True

    def __post_init__(self) -> None:
        if not self.contract_id or not self.owner_id or not self.representative_id:
            raise ValueError("contract, owner and representative identifiers are required")
        if self.version < 1:
            raise ValueError("contract version must be positive")
        if self.expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")


def evaluate_authority(
    contract: AuthorityContract,
    request: TaskRequest,
    *,
    now: datetime | None = None,
) -> AuthorityDecision:
    """Return a decision without executing the requested action.

    Unknown or absent authority is never interpreted as permission.
    """
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if contract.revoked or instant >= contract.expires_at:
        return AuthorityDecision.DENY
    if request.task_type not in contract.allowed_tasks or request.tool not in contract.allowed_tools:
        return AuthorityDecision.DENY
    if not request.data_scopes.issubset(contract.data_scopes):
        return AuthorityDecision.DENY

    approval_required = (
        (request.high_impact and contract.require_approval_for_high_impact)
        or (request.irreversible and contract.require_approval_for_irreversible)
    )
    if approval_required and not request.human_approval_present:
        return AuthorityDecision.HOLD
    return AuthorityDecision.ALLOW
