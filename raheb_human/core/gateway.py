"""Side-effect admission boundary. This module does not execute tools."""

from dataclasses import dataclass

from .authority import AuthorityContract, AuthorityDecision, TaskRequest, evaluate_authority


@dataclass(frozen=True)
class AdmissionResult:
    decision: AuthorityDecision
    side_effect_permitted: bool
    reason: str


def admit_action(
    contract: AuthorityContract | None,
    request: TaskRequest,
) -> AdmissionResult:
    if contract is None:
        return AdmissionResult(AuthorityDecision.HOLD, False, "authority contract is missing")
    decision = evaluate_authority(contract, request)
    if decision == AuthorityDecision.ALLOW:
        return AdmissionResult(decision, True, "current scoped authority satisfied")
    if decision == AuthorityDecision.HOLD:
        return AdmissionResult(decision, False, "human approval required")
    return AdmissionResult(decision, False, "authority denied or insufficient")
