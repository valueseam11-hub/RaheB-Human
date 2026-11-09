"Human-in-the-loop visual attestation primitives. Policy reference only; no media ingestion or physical control."
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import FrozenSet

class RiskLevel(str, Enum):
    LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"; UNKNOWN="UNKNOWN"
class ReviewRoute(str, Enum):
    CONTINUE="CONTINUE"; HUMAN_REVIEW="HUMAN_REVIEW"; HOLD="HOLD"
class HumanVerdict(str, Enum):
    OBSERVED="OBSERVED"; NOT_OBSERVED="NOT_OBSERVED"; UNCERTAIN="UNCERTAIN"; EVIDENCE_UNUSABLE="EVIDENCE_UNUSABLE"; DISAGREES_WITH_MODEL="DISAGREES_WITH_MODEL"
class FeedbackStatus(str, Enum):
    PENDING_VALIDATION="PENDING_VALIDATION"; ACCEPTED_FOR_EVALUATION="ACCEPTED_FOR_EVALUATION"; REJECTED="REJECTED"

@dataclass(frozen=True)
class VisualEvidence:
    evidence_id:str; subject_id:str; media_digest:str; media_type:str; captured_at:datetime
    source_id:str; source_integrity:str; original_preserved:bool
    transformation_history:tuple[str,...]=(); related_stream_ids:tuple[str,...]=(); context_complete:bool=False
    def validate(self):
        if not all((self.evidence_id,self.subject_id,self.media_digest,self.media_type,self.source_id)): raise ValueError("evidence identity, digest, media type and source are required")
        if len(self.media_digest)<32: raise ValueError("media_digest must be a verifiable digest")
        if self.captured_at.tzinfo is None: raise ValueError("captured_at must be timezone-aware")
        if not self.original_preserved: raise ValueError("original evidence must be preserved")
        if self.source_integrity not in {"VERIFIED","UNVERIFIED","COMPROMISED","UNKNOWN"}: raise ValueError("unsupported source integrity state")

@dataclass(frozen=True)
class ModelAssessment:
    assessment_id:str; model_id:str; model_version:str; output_digest:str
    uncertainty:float|None; uncertainty_method:str|None; risk:RiskLevel
    detected_conflicts:tuple[str,...]=()
    def validate(self):
        if not all((self.assessment_id,self.model_id,self.model_version,self.output_digest)): raise ValueError("assessment identity and output digest are required")
        if self.uncertainty is not None and not 0<=self.uncertainty<=1: raise ValueError("uncertainty must be between 0 and 1")
        if self.uncertainty is not None and not self.uncertainty_method: raise ValueError("uncertainty method is required")

@dataclass(frozen=True)
class AttestationPolicy:
    uncertainty_review_threshold:float=.30
    mandatory_review_risks:FrozenSet[RiskLevel]=frozenset({RiskLevel.HIGH,RiskLevel.CRITICAL,RiskLevel.UNKNOWN})
    require_independent_first:bool=True
    max_open_reviews_per_reviewer:int=20
    def __post_init__(self):
        if not 0<=self.uncertainty_review_threshold<=1: raise ValueError("threshold must be between 0 and 1")
        if self.max_open_reviews_per_reviewer<1: raise ValueError("review capacity must be positive")

@dataclass(frozen=True)
class ReviewRouteDecision:
    route:ReviewRoute; reasons:tuple[str,...]

def route_for_attestation(assessment:ModelAssessment,policy:AttestationPolicy,*,evidence_available:bool,reviewer_capacity_available:bool=True)->ReviewRouteDecision:
    assessment.validate()
    if not evidence_available: return ReviewRouteDecision(ReviewRoute.HOLD,("visual evidence is missing",))
    reasons=[]
    if assessment.risk in policy.mandatory_review_risks: reasons.append(f"{assessment.risk.value.lower()} risk requires human review regardless of confidence")
    if assessment.uncertainty is None: reasons.append("model uncertainty is unavailable")
    elif assessment.uncertainty>=policy.uncertainty_review_threshold: reasons.append("uncertainty meets configured review threshold")
    if assessment.detected_conflicts: reasons.append("conflicting evidence or model outputs require review")
    if reasons and not reviewer_capacity_available: return ReviewRouteDecision(ReviewRoute.HOLD,tuple(reasons+["review capacity unavailable"]))
    return ReviewRouteDecision(ReviewRoute.HUMAN_REVIEW if reasons else ReviewRoute.CONTINUE,tuple(reasons or ["configured low-risk routing conditions satisfied"]))

@dataclass(frozen=True)
class HumanAttestation:
    attestation_id:str; evidence_id:str; assessment_id:str; reviewer_id:str; verdict:HumanVerdict
    rationale:str; reviewed_at:datetime; evidence_digest:str; assessment_output_digest:str
    saw_model_output_first:bool
    def validate(self,policy:AttestationPolicy):
        if not all((self.attestation_id,self.evidence_id,self.assessment_id,self.reviewer_id,self.rationale.strip())): raise ValueError("attestation identity, reviewer and rationale are required")
        if self.reviewed_at.tzinfo is None: raise ValueError("review time must be timezone-aware")
        if not self.evidence_digest or not self.assessment_output_digest: raise ValueError("attestation must bind exact evidence and model output digests")
        if policy.require_independent_first and self.saw_model_output_first: raise ValueError("independent-first review policy was not followed")

@dataclass(frozen=True)
class Intervention:
    intervention_id:str; attestation_id:str; reviewer_id:str; reason:str; safe_state:str; authorised:bool; occurred_at:datetime

def validate_intervention(intervention:Intervention):
    if not intervention.authorised: raise PermissionError("reviewer is not authorised to trigger this intervention")
    if not all((intervention.intervention_id,intervention.attestation_id,intervention.reviewer_id,intervention.reason.strip(),intervention.safe_state.strip())): raise ValueError("intervention lineage and safe state are required")
    if intervention.occurred_at.tzinfo is None: raise ValueError("intervention time must be timezone-aware")

@dataclass(frozen=True)
class CorrectionFeedback:
    feedback_id:str; attestation_id:str; corrected_label:str; reviewer_id:str
    status:FeedbackStatus=FeedbackStatus.PENDING_VALIDATION

def validate_feedback_for_training(feedback:CorrectionFeedback):
    if feedback.status is not FeedbackStatus.ACCEPTED_FOR_EVALUATION: raise ValueError("human correction is not ground truth; independent validation is required")
    if not all((feedback.feedback_id,feedback.attestation_id,feedback.corrected_label.strip(),feedback.reviewer_id)): raise ValueError("feedback lineage is incomplete")
