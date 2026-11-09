"""Work redistribution and capability development primitives.

Measures where human effort moves when AI enters a workflow and protects
opportunities to build professional judgment. No employee scoring or payroll
prediction is performed here.
"""
from dataclasses import dataclass
from enum import Enum

class EffortKind(str, Enum):
    AI_PREPARATION = "AI_PREPARATION"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    HUMAN_CORRECTION = "HUMAN_CORRECTION"
    EXCEPTION_HANDLING = "EXCEPTION_HANDLING"
    COORDINATION = "COORDINATION"
    TRAINING = "TRAINING"
    HUMAN_JUDGMENT = "HUMAN_JUDGMENT"

@dataclass(frozen=True)
class WorkloadShift:
    workflow_id: str
    baseline_human_minutes: int
    ai_assisted_human_minutes: int
    review_minutes: int
    correction_minutes: int
    exception_minutes: int
    coordination_minutes: int
    training_minutes: int = 0
    completed_cases: int = 1
    baseline_quality_score: float | None = None
    assisted_quality_score: float | None = None
    unresolved_exceptions: int = 0
    def __post_init__(self):
        if not self.workflow_id.strip(): raise ValueError("workflow_id required")
        nums=(self.baseline_human_minutes,self.ai_assisted_human_minutes,self.review_minutes,self.correction_minutes,self.exception_minutes,self.coordination_minutes,self.training_minutes,self.unresolved_exceptions)
        if any(n < 0 for n in nums): raise ValueError("minutes and exception counts cannot be negative")
        if self.completed_cases < 1: raise ValueError("completed_cases must be positive")
        for q in (self.baseline_quality_score,self.assisted_quality_score):
            if q is not None and not 0 <= q <= 1: raise ValueError("quality scores must be between 0 and 1")
    @property
    def total_assisted_human_minutes(self) -> int:
        return self.ai_assisted_human_minutes+self.review_minutes+self.correction_minutes+self.exception_minutes+self.coordination_minutes
    @property
    def net_human_minutes_saved(self) -> int:
        return self.baseline_human_minutes-self.total_assisted_human_minutes
    @property
    def human_effort_per_case(self) -> float:
        return self.total_assisted_human_minutes/self.completed_cases
    @property
    def quality_change(self) -> float | None:
        if self.baseline_quality_score is None or self.assisted_quality_score is None: return None
        return self.assisted_quality_score-self.baseline_quality_score
    @property
    def requires_workflow_review(self) -> bool:
        return self.net_human_minutes_saved <= 0 or self.unresolved_exceptions > 0 or (self.quality_change is not None and self.quality_change < 0)

class LearningMode(str, Enum):
    EXPLAIN = "EXPLAIN"
    GUIDED_PRACTICE = "GUIDED_PRACTICE"
    SHADOW_REVIEW = "SHADOW_REVIEW"
    HUMAN_PERFORMANCE_CHECK = "HUMAN_PERFORMANCE_CHECK"

@dataclass(frozen=True)
class LearningOpportunity:
    skill_id: str
    task_id: str
    learning_objective: str
    mode: LearningMode
    human_practice_required: bool = True
    ai_may_complete_assessment: bool = False
    evidence_required: bool = True
    def __post_init__(self):
        if not all((self.skill_id.strip(),self.task_id.strip(),self.learning_objective.strip())): raise ValueError("skill, task and objective are required")
        if self.ai_may_complete_assessment: raise ValueError("AI cannot attest to the human learner’s competence")

@dataclass(frozen=True)
class SkillEvidence:
    skill_id: str
    learner_id: str
    assessor_id: str
    assessment_method: str
    evidence_reference: str
    outcome: str
    assessed_at: str
    def __post_init__(self):
        if not all((self.skill_id,self.learner_id,self.assessor_id,self.assessment_method,self.evidence_reference,self.outcome,self.assessed_at)): raise ValueError("skill evidence must be complete and attributable")
        if self.outcome not in {"DEMONSTRATED","DEVELOPING","NOT_DEMONSTRATED","INCONCLUSIVE"}: raise ValueError("unsupported skill evidence outcome")

@dataclass(frozen=True)
class WorkforceImpactSummary:
    workflow_count: int
    total_cases: int
    total_net_human_minutes_saved: int
    workflows_requiring_review: int
    unresolved_exceptions: int
    @classmethod
    def from_workflows(cls, workflows: tuple[WorkloadShift,...]) -> "WorkforceImpactSummary":
        return cls(len(workflows),sum(w.completed_cases for w in workflows),sum(w.net_human_minutes_saved for w in workflows),sum(w.requires_workflow_review for w in workflows),sum(w.unresolved_exceptions for w in workflows))

def describe_workforce_guardrails() -> tuple[str,...]:
    return (
        "Do not infer employee replaceability, rank workers or make employment decisions from workflow metrics.",
        "Report workflow-level outcomes; individual contribution disclosure requires a separate lawful purpose and explicit access policy.",
        "Count review, correction, exception handling and coordination as human work.",
        "Preserve negative time savings and quality regressions; do not report gross AI throughput as productivity.",
        "Create supervised practice opportunities where automation would otherwise remove a learning step.",
        "Skill claims require attributable human performance evidence; AI completion is not proof of human competence.",
    )

