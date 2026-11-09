"""Evidence-led career opportunity intelligence and job-search preparation.

This is a planning aid, not an ATS bypass, hiring predictor, or autonomous
application agent. It preserves source dates, uncertainty and human agency.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SignalConfidence(str, Enum):
    OBSERVED = "OBSERVED"
    REPORTED = "REPORTED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class ApplicationStage(str, Enum):
    RESEARCH = "RESEARCH"
    PREPARATION = "PREPARATION"
    SUBMITTED = "SUBMITTED"
    SCREENING = "SCREENING"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    CLOSED = "CLOSED"


@dataclass(frozen=True)
class LabourMarketSignal:
    signal_id: str
    description: str
    source_reference: str
    published_at: datetime
    geography: str
    occupation_or_sector: str
    confidence: SignalConfidence
    observed_or_projected: str

    def __post_init__(self):
        if not all((self.signal_id.strip(), self.description.strip(),
                    self.source_reference.strip(), self.geography.strip(),
                    self.occupation_or_sector.strip(), self.observed_or_projected.strip())):
            raise ValueError("signal identity, source, scope and description are required")
        if self.published_at.tzinfo is None:
            raise ValueError("signal publication time must be timezone-aware")
        if self.observed_or_projected not in {"OBSERVED", "PROJECTED", "SCENARIO"}:
            raise ValueError("signal must be labelled OBSERVED, PROJECTED or SCENARIO")


@dataclass(frozen=True)
class OpportunityRequirement:
    requirement_id: str
    description: str
    requirement_type: str
    source_excerpt: str
    essential: bool = False

    def __post_init__(self):
        if not all((self.requirement_id.strip(), self.description.strip(),
                    self.requirement_type.strip(), self.source_excerpt.strip())):
            raise ValueError("each requirement needs its source wording")
        if self.requirement_type not in {"SKILL", "TASK", "EXPERIENCE", "CREDENTIAL", "WORK_CONDITION"}:
            raise ValueError("unsupported requirement type")


@dataclass(frozen=True)
class CandidateEvidence:
    requirement_id: str
    evidence_reference: str
    evidence_owner: str
    context: str
    outcome: str
    verified: bool = False

    def __post_init__(self):
        if not all((self.requirement_id.strip(), self.evidence_reference.strip(),
                    self.evidence_owner.strip(), self.context.strip(), self.outcome.strip())):
            raise ValueError("candidate evidence must be attributable and contextualised")


@dataclass(frozen=True)
class OpportunityAssessment:
    opportunity_id: str
    employer: str
    role_title: str
    source_reference: str
    retrieved_at: datetime
    requirements: tuple[OpportunityRequirement, ...]
    candidate_evidence: tuple[CandidateEvidence, ...]
    owner_interest: str

    def __post_init__(self):
        if not all((self.opportunity_id.strip(), self.employer.strip(), self.role_title.strip(),
                    self.source_reference.strip(), self.owner_interest.strip())):
            raise ValueError("opportunity identity, source and owner interest are required")
        if self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at must be timezone-aware")
        ids = [item.requirement_id for item in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("requirement IDs must be unique")
        unknown = {item.requirement_id for item in self.candidate_evidence} - set(ids)
        if unknown:
            raise ValueError("candidate evidence must map to a sourced requirement")

    @property
    def requirements_with_evidence(self) -> tuple[str, ...]:
        return tuple(sorted({item.requirement_id for item in self.candidate_evidence}))

    @property
    def requirements_without_evidence(self) -> tuple[str, ...]:
        evidenced = set(self.requirements_with_evidence)
        return tuple(item.requirement_id for item in self.requirements
                     if item.requirement_id not in evidenced)


@dataclass(frozen=True)
class HiringProcessQuestions:
    ai_use_policy: str
    assessment_method: str
    human_review_available: bool | None
    data_use_clarity: str
    accommodation_route: str = ""

    def __post_init__(self):
        if not self.ai_use_policy.strip() or not self.assessment_method.strip():
            raise ValueError("ask about AI-use policy and assessment method")
        if self.human_review_available is None and not self.data_use_clarity.strip():
            raise ValueError("record whether data use and human review are clear")


@dataclass(frozen=True)
class ApplicationRecord:
    application_id: str
    opportunity_id: str
    stage: ApplicationStage
    updated_at: datetime
    human_confirmed: bool
    submitted_by_owner: bool
    notes: str = ""

    def __post_init__(self):
        if not self.application_id.strip() or not self.opportunity_id.strip():
            raise ValueError("application and opportunity IDs are required")
        if self.updated_at.tzinfo is None:
            raise ValueError("updated_at must be timezone-aware")
        if self.stage == ApplicationStage.SUBMITTED and not self.submitted_by_owner:
            raise ValueError("submission must be explicitly performed by the owner")


def build_opportunity_summary(assessment: OpportunityAssessment) -> dict[str, object]:
    """Summarise sourced requirements without ranking the person or predicting hiring."""
    evidence_by_req = {item.requirement_id: item for item in assessment.candidate_evidence}
    requirement_rows = []
    for req in assessment.requirements:
        evidence = evidence_by_req.get(req.requirement_id)
        requirement_rows.append({
            "requirement_id": req.requirement_id,
            "description": req.description,
            "type": req.requirement_type,
            "essential": req.essential,
            "evidence_status": "EVIDENCE_PROVIDED" if evidence else "NOT_YET_EVIDENCED",
            "evidence_reference": evidence.evidence_reference if evidence else None,
            "verified": evidence.verified if evidence else False,
        })
    return {
        "employer": assessment.employer,
        "role_title": assessment.role_title,
        "source_reference": assessment.source_reference,
        "retrieved_at": assessment.retrieved_at.isoformat(),
        "owner_interest": assessment.owner_interest,
        "requirements": requirement_rows,
        "requirements_without_evidence": list(assessment.requirements_without_evidence),
        "limitations": [
            "A job title is not a reliable substitute for the tasks and requirements in the source.",
            "Not-yet-evidenced does not mean the person lacks the skill.",
            "AI-generated application language must be checked against the person's real experience.",
            "This assessment does not predict ATS passage, interview success, job security or hiring decisions.",
            "Labour-market signals must retain source, date, geography and observed-versus-projected status.",
        ],
    }
