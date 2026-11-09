"""Owner-directed career transition and human-interaction boundary primitives.

This module supports planning and evidence organisation. It does not predict
layoffs, rank replaceability, score employability, or make hiring decisions.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SkillEvidenceState(str, Enum):
    DEMONSTRATED = "DEMONSTRATED"
    DEVELOPING = "DEVELOPING"
    NOT_YET_EVIDENCED = "NOT_YET_EVIDENCED"
    DISPUTED = "DISPUTED"


class TransitionActionKind(str, Enum):
    LEARN = "LEARN"
    PRACTISE = "PRACTISE"
    SHADOW = "SHADOW"
    SEEK_MENTORSHIP = "SEEK_MENTORSHIP"
    BUILD_PORTFOLIO_EVIDENCE = "BUILD_PORTFOLIO_EVIDENCE"
    EXPLORE_ROLE = "EXPLORE_ROLE"


class HumanInteractionMode(str, Enum):
    HUMAN_OWNED = "HUMAN_OWNED"
    AI_PREPARE_ONLY = "AI_PREPARE_ONLY"
    AI_ASSISTED_WITH_APPROVAL = "AI_ASSISTED_WITH_APPROVAL"


@dataclass(frozen=True)
class SkillRequirement:
    skill_id: str
    description: str
    source_reference: str
    source_published_at: datetime
    required_for_goal: bool = True

    def __post_init__(self):
        if not all((self.skill_id.strip(), self.description.strip(), self.source_reference.strip())):
            raise ValueError("skill requirement identity, description and source are required")
        if self.source_published_at.tzinfo is None:
            raise ValueError("source publication time must be timezone-aware")


@dataclass(frozen=True)
class SkillEvidenceRecord:
    skill_id: str
    state: SkillEvidenceState
    evidence_reference: str
    demonstrated_by: str
    assessed_at: datetime
    context: str

    def __post_init__(self):
        if not all((self.skill_id.strip(), self.evidence_reference.strip(), self.demonstrated_by.strip(), self.context.strip())):
            raise ValueError("skill evidence must be attributable and contextualised")
        if self.assessed_at.tzinfo is None:
            raise ValueError("skill evidence timestamp must be timezone-aware")
        if self.state == SkillEvidenceState.DEMONSTRATED and not self.evidence_reference:
            raise ValueError("demonstrated skill requires an evidence reference")


@dataclass(frozen=True)
class DevelopmentAction:
    action_id: str
    skill_id: str
    kind: TransitionActionKind
    description: str
    owner_selected: bool = True
    human_practice_required: bool = True

    def __post_init__(self):
        if not all((self.action_id.strip(), self.skill_id.strip(), self.description.strip())):
            raise ValueError("development action fields are required")
        if self.kind in {TransitionActionKind.PRACTISE, TransitionActionKind.SHADOW} and not self.human_practice_required:
            raise ValueError("practice and shadowing must involve the human learner")


@dataclass(frozen=True)
class CareerTransitionPlan:
    owner_id: str
    current_role: str
    owner_defined_goal: str
    prepared_at: datetime
    skill_requirements: tuple[SkillRequirement, ...]
    skill_evidence: tuple[SkillEvidenceRecord, ...]
    development_actions: tuple[DevelopmentAction, ...]

    def __post_init__(self):
        if not all((self.owner_id.strip(), self.current_role.strip(), self.owner_defined_goal.strip())):
            raise ValueError("owner, current role and owner-defined goal are required")
        if self.prepared_at.tzinfo is None:
            raise ValueError("plan timestamp must be timezone-aware")
        requirement_ids = [item.skill_id for item in self.skill_requirements]
        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError("skill requirement IDs must be unique")
        unknown_skills = {
            item.skill_id for item in self.development_actions
        } - set(requirement_ids)
        if unknown_skills:
            raise ValueError("development actions must map to a stated skill requirement")

    def evidence_state_for(self, skill_id: str) -> SkillEvidenceState:
        records = [item for item in self.skill_evidence if item.skill_id == skill_id]
        if not records:
            return SkillEvidenceState.NOT_YET_EVIDENCED
        # Disputes are preserved and take precedence over an unsupported positive claim.
        if any(item.state == SkillEvidenceState.DISPUTED for item in records):
            return SkillEvidenceState.DISPUTED
        if any(item.state == SkillEvidenceState.DEMONSTRATED for item in records):
            return SkillEvidenceState.DEMONSTRATED
        if any(item.state == SkillEvidenceState.DEVELOPING for item in records):
            return SkillEvidenceState.DEVELOPING
        return SkillEvidenceState.NOT_YET_EVIDENCED

    @property
    def skills_requiring_development(self) -> tuple[str, ...]:
        return tuple(
            requirement.skill_id for requirement in self.skill_requirements
            if requirement.required_for_goal
            and self.evidence_state_for(requirement.skill_id) in {
                SkillEvidenceState.DEVELOPING,
                SkillEvidenceState.NOT_YET_EVIDENCED,
                SkillEvidenceState.DISPUTED,
            }
        )


@dataclass(frozen=True)
class HumanInteractionBoundary:
    interaction_type: str
    mode: HumanInteractionMode
    owner_id: str
    purpose: str
    approved_at: datetime | None = None
    expires_at: datetime | None = None

    def __post_init__(self):
        if not all((self.interaction_type.strip(), self.owner_id.strip(), self.purpose.strip())):
            raise ValueError("interaction type, owner and purpose are required")
        if self.mode == HumanInteractionMode.AI_ASSISTED_WITH_APPROVAL:
            if self.approved_at is None or self.expires_at is None:
                raise ValueError("AI-assisted interaction requires explicit approval and expiry")
            if self.approved_at.tzinfo is None or self.expires_at.tzinfo is None:
                raise ValueError("approval timestamps must be timezone-aware")
            if self.expires_at <= self.approved_at:
                raise ValueError("approval expiry must follow approval time")


def build_transition_summary(plan: CareerTransitionPlan) -> dict[str, object]:
    """Return an owner-facing plan summary, not a job-loss or employability score."""
    return {
        "current_role": plan.current_role,
        "owner_defined_goal": plan.owner_defined_goal,
        "requirements": tuple({
            "skill_id": item.skill_id,
            "description": item.description,
            "source_reference": item.source_reference,
            "source_published_at": item.source_published_at.isoformat(),
            "evidence_state": plan.evidence_state_for(item.skill_id).value,
            "required_for_goal": item.required_for_goal,
        } for item in plan.skill_requirements),
        "skills_requiring_development": plan.skills_requiring_development,
        "development_action_count": len(plan.development_actions),
        "limitations": (
            "A skill requirement is only as current and relevant as its cited source.",
            "Absence of evidence is not evidence of absence or lack of ability.",
            "This plan does not predict job loss, employability, salary, hiring outcomes or role availability.",
            "The owner defines the goal and selects development actions; no career path is imposed.",
        ),
    }
