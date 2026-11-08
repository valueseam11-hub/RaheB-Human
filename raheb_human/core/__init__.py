"""Core authority, consent, capability, evidence and control-plane primitives."""

from .authority import AuthorityContract, AuthorityDecision, TaskRequest, evaluate_authority
from .capability import CapabilityAssessment, CapabilityStatus, HumanCredential
from .consent import ConsentGrant, ConsentPurpose, consent_allows
from .control_plane import (
    ControlPlaneResult, HumanApproval, OwnerIdentity, RepresentativeControlPlane,
    RepresentativeRecord, RepresentativeSpec, RepresentativeState,
)
from .evidence import EvidenceLedger
from .gateway import AdmissionResult, admit_action
from .knowledge import KnowledgeDocument, KnowledgeHit, KnowledgeSource, KnowledgeState, PersonalKnowledgeStore

__all__ = [
    "AuthorityContract", "AuthorityDecision", "TaskRequest", "evaluate_authority",
    "CapabilityAssessment", "CapabilityStatus", "HumanCredential",
    "ConsentGrant", "ConsentPurpose", "consent_allows",
    "ControlPlaneResult", "HumanApproval", "OwnerIdentity",
    "RepresentativeControlPlane", "RepresentativeRecord", "RepresentativeSpec",
    "RepresentativeState", "EvidenceLedger", "AdmissionResult", "admit_action",
    "KnowledgeDocument", "KnowledgeHit", "KnowledgeSource", "KnowledgeState", "PersonalKnowledgeStore",
]
