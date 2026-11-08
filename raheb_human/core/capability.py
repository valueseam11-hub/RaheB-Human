"""Separate human credentials from evidence-backed AI capability."""

from dataclasses import dataclass
from enum import StrEnum


class CapabilityStatus(StrEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    TESTED = "TESTED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class HumanCredential:
    holder_id: str
    credential_type: str
    issuer: str
    credential_reference: str
    verified: bool = False


@dataclass(frozen=True)
class CapabilityAssessment:
    representative_id: str
    capability: str
    scope: str
    assessment_id: str
    status: CapabilityStatus
    test_suite_version: str
    evidence_digest: str

    def supports(self, capability: str, scope: str) -> bool:
        return (
            self.capability == capability
            and self.scope == scope
            and self.status == CapabilityStatus.TESTED
            and bool(self.assessment_id and self.test_suite_version and self.evidence_digest)
        )


def human_credential_implies_ai_capability(_credential: HumanCredential) -> bool:
    """Intentionally always false: human qualifications do not transfer to AI."""
    return False
