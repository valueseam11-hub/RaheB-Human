"""In-memory reference implementation of the Personal Representative Control Plane.

This module models lifecycle and admission. It deliberately does not execute tools,
authenticate callers, or persist state. Production adapters must provide those controls.
"""
from __future__ import annotations
import hashlib
import json
import secrets
import threading
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from .authority import AuthorityContract, AuthorityDecision, TaskRequest, evaluate_authority
from .capability import CapabilityAssessment
from .consent import ConsentGrant, ConsentPurpose, consent_allows
from .evidence import EvidenceLedger


class RepresentativeState(StrEnum):
    CONFIGURED = "CONFIGURED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class OwnerIdentity:
    owner_id: str
    verified: bool


@dataclass(frozen=True)
class RepresentativeSpec:
    display_name: str
    professional_role: str
    approved_knowledge_refs: tuple[str, ...]
    ai_disclosure_enabled: bool = True

    def __post_init__(self) -> None:
        if not self.display_name.strip() or not self.professional_role.strip():
            raise ValueError("representative name and professional role are required")
        if not self.approved_knowledge_refs:
            raise ValueError("at least one owner-approved knowledge reference is required")
        if not self.ai_disclosure_enabled:
            raise ValueError("AI identity disclosure is mandatory")


@dataclass(frozen=True)
class RepresentativeRecord:
    representative_id: str
    owner_id: str
    spec: RepresentativeSpec
    version: int
    state: RepresentativeState
    authority_contract_id: str | None = None
    authority_contract_version: int | None = None


@dataclass(frozen=True)
class HumanApproval:
    approval_id: str
    owner_id: str
    representative_id: str
    representative_version: int
    authority_contract_id: str
    authority_contract_version: int
    task_digest: str
    expires_at: datetime


@dataclass(frozen=True)
class ControlPlaneResult:
    decision: AuthorityDecision
    side_effect_permitted: bool
    reason: str


def _task_digest(request: TaskRequest) -> str:
    body = {
        "task_type": request.task_type,
        "tool": request.tool,
        "data_scopes": sorted(request.data_scopes),
        "high_impact": request.high_impact,
        "irreversible": request.irreversible,
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class RepresentativeControlPlane:
    """Thread-safe in-memory lifecycle and admission coordinator.

    One process-local lock supports deterministic tests, not distributed
    transactions, authenticated sessions or durable revocation state.
    """

    def __init__(self, evidence: EvidenceLedger | None = None) -> None:
        self.evidence = evidence or EvidenceLedger()
        self._representatives: dict[str, RepresentativeRecord] = {}
        self._stop_switch: dict[str, bool] = {}
        self._approvals: dict[str, HumanApproval] = {}
        self._used_approvals: set[str] = set()
        self._pending_tasks: dict[str, set[str]] = {}
        self._cancelled_tasks: set[str] = set()
        self._lock = threading.RLock()

    def get(self, representative_id: str) -> RepresentativeRecord | None:
        with self._lock:
            return self._representatives.get(representative_id)

    def register(self, owner: OwnerIdentity, representative_id: str,
                 spec: RepresentativeSpec) -> RepresentativeRecord:
        with self._lock:
            if not owner.verified:
                raise PermissionError("verified owner identity is required")
            if not representative_id or representative_id in self._representatives:
                raise ValueError("representative ID must be unique and non-empty")
            record = RepresentativeRecord(representative_id, owner.owner_id, spec, 1,
                                          RepresentativeState.CONFIGURED)
            self._representatives[representative_id] = record
            self._stop_switch[representative_id] = True
            self._pending_tasks[representative_id] = set()
            self.evidence.append("REPRESENTATIVE_REGISTERED", representative_id, {
                "owner_id": owner.owner_id,
                "representative_version": record.version,
                "ai_disclosure": spec.ai_disclosure_enabled,
                "approved_knowledge_ref_count": len(spec.approved_knowledge_refs),
            })
            return record

    def activate(self, owner_id: str, representative_id: str,
                 contract: AuthorityContract, consent_grants: tuple[ConsentGrant, ...],
                 *, now: datetime | None = None) -> RepresentativeRecord:
        instant = now or datetime.now(timezone.utc)
        with self._lock:
            record = self._require_owner(owner_id, representative_id)
            if record.state == RepresentativeState.REVOKED:
                raise PermissionError("revoked representatives cannot be reactivated")
            if not consent_allows(consent_grants, owner_id,
                                  ConsentPurpose.SERVICE_PROCESSING, now=instant):
                raise PermissionError("current service-processing consent is required")
            if contract.owner_id != owner_id or contract.representative_id != representative_id:
                raise PermissionError("authority contract identity does not match representative")
            if contract.revoked or instant >= contract.expires_at:
                raise PermissionError("authority contract is revoked or expired")
            updated = replace(record, version=record.version + 1,
                              state=RepresentativeState.ACTIVE,
                              authority_contract_id=contract.contract_id,
                              authority_contract_version=contract.version)
            self._representatives[representative_id] = updated
            self._stop_switch[representative_id] = False
            self.evidence.append("REPRESENTATIVE_ACTIVATED", representative_id, {
                "owner_id": owner_id,
                "representative_version": updated.version,
                "authority_contract_id": contract.contract_id,
                "authority_contract_version": contract.version,
            }, occurred_at=instant)
            return updated

    def pause(self, owner_id: str, representative_id: str) -> RepresentativeRecord:
        return self._stop(owner_id, representative_id, revoke=False)

    def revoke(self, owner_id: str, representative_id: str) -> RepresentativeRecord:
        return self._stop(owner_id, representative_id, revoke=True)

    def _stop(self, owner_id: str, representative_id: str,
              *, revoke: bool) -> RepresentativeRecord:
        with self._lock:
            record = self._require_owner(owner_id, representative_id)
            if record.state == RepresentativeState.REVOKED:
                return record
            state = RepresentativeState.REVOKED if revoke else RepresentativeState.PAUSED
            updated = replace(record, version=record.version + 1, state=state)
            self._representatives[representative_id] = updated
            self._stop_switch[representative_id] = True
            pending = self._pending_tasks.get(representative_id, set())
            cancelled_count = len(pending)
            self._cancelled_tasks.update(pending)
            pending.clear()
            self._approvals = {key: value for key, value in self._approvals.items()
                               if value.representative_id != representative_id}
            self.evidence.append("REPRESENTATIVE_REVOKED" if revoke else "REPRESENTATIVE_PAUSED",
                                 representative_id, {
                "owner_id": owner_id,
                "representative_version": updated.version,
                "cancelled_pending_task_count": cancelled_count,
            })
            return updated

    def register_pending_task(self, owner_id: str, representative_id: str,
                              task_id: str) -> None:
        with self._lock:
            record = self._require_owner(owner_id, representative_id)
            self._assert_active(record)
            if not task_id:
                raise ValueError("task_id is required")
            self._pending_tasks[representative_id].add(task_id)
            self.evidence.append("TASK_QUEUED", representative_id, {"task_id": task_id})

    def was_task_cancelled(self, task_id: str) -> bool:
        with self._lock:
            return task_id in self._cancelled_tasks

    def approve_task(self, owner_id: str, representative_id: str,
                     request: TaskRequest, contract: AuthorityContract, *,
                     expires_in: timedelta = timedelta(minutes=5),
                     now: datetime | None = None) -> HumanApproval:
        instant = now or datetime.now(timezone.utc)
        if expires_in <= timedelta(0) or expires_in > timedelta(minutes=15):
            raise ValueError("approval expiry must be between 0 and 15 minutes")
        with self._lock:
            record = self._require_owner(owner_id, representative_id)
            self._assert_active(record)
            self._assert_contract_binding(record, contract)
            if not (request.high_impact or request.irreversible):
                raise ValueError("approval tickets are reserved for high-impact or irreversible tasks")
            approval = HumanApproval(
                secrets.token_urlsafe(24), owner_id, representative_id, record.version,
                contract.contract_id, contract.version, _task_digest(request),
                instant + expires_in,
            )
            self._approvals[approval.approval_id] = approval
            self.evidence.append("HUMAN_APPROVAL_ISSUED", representative_id, {
                "approval_id_digest": hashlib.sha256(approval.approval_id.encode()).hexdigest(),
                "task_digest": approval.task_digest,
                "representative_version": record.version,
                "authority_contract_version": contract.version,
                "expires_at": approval.expires_at.isoformat(),
            }, occurred_at=instant)
            return approval

    def admit(self, owner_id: str, representative_id: str, request: TaskRequest,
              contract: AuthorityContract | None, capability: CapabilityAssessment | None,
              consent_grants: tuple[ConsentGrant, ...], *,
              required_capability: str, required_scope: str,
              approval_id: str | None = None,
              expected_representative_version: int | None = None,
              now: datetime | None = None) -> ControlPlaneResult:
        instant = now or datetime.now(timezone.utc)
        with self._lock:
            record = self._representatives.get(representative_id)
            if record is None or record.owner_id != owner_id:
                return ControlPlaneResult(AuthorityDecision.HOLD, False,
                                          "representative identity is unknown")
            if record.state != RepresentativeState.ACTIVE or self._stop_switch.get(representative_id, True):
                return ControlPlaneResult(AuthorityDecision.DENY, False,
                                          "representative is paused, revoked or stopped")
            if expected_representative_version != record.version:
                return ControlPlaneResult(AuthorityDecision.HOLD, False,
                                          "representative version is missing or stale")
            if not consent_allows(consent_grants, owner_id,
                                  ConsentPurpose.SERVICE_PROCESSING, now=instant):
                return ControlPlaneResult(AuthorityDecision.HOLD, False,
                                          "service-processing consent is absent or withdrawn")
            if capability is None or capability.representative_id != representative_id or not capability.supports(
                required_capability, required_scope
            ):
                return ControlPlaneResult(AuthorityDecision.HOLD, False,
                                          "scoped AI capability evidence is absent or insufficient")
            if contract is None:
                return ControlPlaneResult(AuthorityDecision.HOLD, False,
                                          "authority contract is missing")
            try:
                self._assert_contract_binding(record, contract)
            except PermissionError:
                return ControlPlaneResult(AuthorityDecision.DENY, False,
                                          "authority contract binding is invalid or stale")

            approval_required = (
                (request.high_impact and contract.require_approval_for_high_impact)
                or (request.irreversible and contract.require_approval_for_irreversible)
            )
            valid_approval = False
            approval = None
            if approval_required:
                approval = self._approvals.get(approval_id or "")
                if approval is None or approval_id in self._used_approvals:
                    return ControlPlaneResult(AuthorityDecision.HOLD, False,
                                              "one-time human approval is missing or already used")
                if (
                    approval.owner_id != owner_id
                    or approval.representative_id != representative_id
                    or approval.representative_version != record.version
                    or approval.authority_contract_id != contract.contract_id
                    or approval.authority_contract_version != contract.version
                    or approval.task_digest != _task_digest(request)
                    or instant >= approval.expires_at
                ):
                    return ControlPlaneResult(AuthorityDecision.HOLD, False,
                                              "human approval is expired or does not match this task")
                valid_approval = True

            checked_request = replace(request, human_approval_present=valid_approval)
            decision = evaluate_authority(contract, checked_request, now=instant)
            if decision != AuthorityDecision.ALLOW:
                return ControlPlaneResult(decision, False,
                                          "authority policy did not allow this action")
            if approval_required and approval is not None:
                self._used_approvals.add(approval.approval_id)
                self._approvals.pop(approval.approval_id, None)
                self.evidence.append("HUMAN_APPROVAL_CONSUMED", representative_id, {
                    "approval_id_digest": hashlib.sha256(approval.approval_id.encode()).hexdigest(),
                    "task_digest": approval.task_digest,
                }, occurred_at=instant)
            self.evidence.append("TASK_ADMITTED", representative_id, {
                "owner_id": owner_id,
                "task_digest": _task_digest(request),
                "representative_version": record.version,
                "authority_contract_id": contract.contract_id,
                "authority_contract_version": contract.version,
                "capability_assessment_id": capability.assessment_id,
                "side_effect_executed": False,
            }, occurred_at=instant)
            return ControlPlaneResult(
                AuthorityDecision.ALLOW, False,
                "admitted for downstream executor; no side effect was executed",
            )

    def _require_owner(self, owner_id: str, representative_id: str) -> RepresentativeRecord:
        record = self._representatives.get(representative_id)
        if record is None or record.owner_id != owner_id:
            raise PermissionError("representative does not belong to this owner")
        return record

    def _assert_active(self, record: RepresentativeRecord) -> None:
        if record.state != RepresentativeState.ACTIVE or self._stop_switch.get(record.representative_id, True):
            raise PermissionError("representative is not active")

    @staticmethod
    def _assert_contract_binding(record: RepresentativeRecord,
                                 contract: AuthorityContract) -> None:
        if (
            contract.owner_id != record.owner_id
            or contract.representative_id != record.representative_id
            or contract.contract_id != record.authority_contract_id
            or contract.version != record.authority_contract_version
            or contract.revoked
        ):
            raise PermissionError("authority contract does not match active representative binding")
