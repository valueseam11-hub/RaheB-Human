"""Work identity and recognition evidence primitives.

Captures the difference between an agreed role and work actually performed.
This is an employee-controlled evidence aid, not a payroll, grading, or
automated employment-decision system.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


class EvidenceStatus(str, Enum):
    SELF_REPORTED = "SELF_REPORTED"
    DOCUMENTED = "DOCUMENTED"
    CORROBORATED = "CORROBORATED"
    DISPUTED = "DISPUTED"
    NOT_VERIFIED = "NOT_VERIFIED"


class RecognitionTopic(str, Enum):
    RESPONSIBILITY = "RESPONSIBILITY"
    WORKLOAD = "WORKLOAD"
    ROLE_SCOPE = "ROLE_SCOPE"
    SKILL_DEVELOPMENT = "SKILL_DEVELOPMENT"
    BUSINESS_OUTCOME = "BUSINESS_OUTCOME"
    COMPENSATION_REVIEW = "COMPENSATION_REVIEW"
    TITLE_OR_LEVEL_REVIEW = "TITLE_OR_LEVEL_REVIEW"


@dataclass(frozen=True)
class RoleExpectation:
    expectation_id: str
    description: str
    source: str
    effective_from: datetime
    formal: bool = True

    def __post_init__(self):
        if not all((self.expectation_id.strip(), self.description.strip(), self.source.strip())):
            raise ValueError("role expectation identity, description and source are required")
        if self.effective_from.tzinfo is None:
            raise ValueError("effective_from must be timezone-aware")


@dataclass(frozen=True)
class WorkRealityEntry:
    entry_id: str
    description: str
    first_observed_at: datetime
    last_observed_at: datetime
    frequency: str
    evidence_status: EvidenceStatus
    evidence_refs: tuple[str, ...] = ()
    ai_assistance_used: bool = False
    human_responsibility: str = ""
    outcome_metric: str | None = None
    baseline_value: float | None = None
    observed_value: float | None = None
    unit: str | None = None

    def __post_init__(self):
        if not all((self.entry_id.strip(), self.description.strip(), self.frequency.strip())):
            raise ValueError("work reality entry fields are required")
        if self.first_observed_at.tzinfo is None or self.last_observed_at.tzinfo is None:
            raise ValueError("observation timestamps must be timezone-aware")
        if self.last_observed_at < self.first_observed_at:
            raise ValueError("last observation cannot precede first observation")
        if (self.baseline_value is None) != (self.observed_value is None):
            raise ValueError("baseline and observed values must be supplied together")
        if self.baseline_value is not None and not self.unit:
            raise ValueError("a unit is required for measured outcomes")
        if self.evidence_status in {EvidenceStatus.DOCUMENTED, EvidenceStatus.CORROBORATED} and not self.evidence_refs:
            raise ValueError("documented or corroborated entries require evidence references")


@dataclass(frozen=True)
class RecognitionCase:
    owner_id: str
    role_title: str
    official_expectations: tuple[RoleExpectation, ...]
    actual_work: tuple[WorkRealityEntry, ...]
    requested_topics: tuple[RecognitionTopic, ...]
    prepared_at: datetime
    owner_approved_for_disclosure: bool = False

    def __post_init__(self):
        if not all((self.owner_id.strip(), self.role_title.strip())):
            raise ValueError("owner and role title are required")
        if self.prepared_at.tzinfo is None:
            raise ValueError("prepared_at must be timezone-aware")
        if not self.actual_work:
            raise ValueError("at least one actual-work entry is required")
        ids = [entry.entry_id for entry in self.actual_work]
        if len(ids) != len(set(ids)):
            raise ValueError("actual-work entry IDs must be unique")

    @property
    def scope_gap_entries(self) -> tuple[WorkRealityEntry, ...]:
        formal = " ".join(item.description.casefold() for item in self.official_expectations)
        return tuple(
            entry for entry in self.actual_work
            if entry.description.casefold() not in formal
        )

    @property
    def evidence_backed_entries(self) -> tuple[WorkRealityEntry, ...]:
        return tuple(
            entry for entry in self.actual_work
            if entry.evidence_status in {EvidenceStatus.DOCUMENTED, EvidenceStatus.CORROBORATED}
        )

    @property
    def measured_outcomes(self) -> tuple[WorkRealityEntry, ...]:
        return tuple(entry for entry in self.actual_work if entry.observed_value is not None)

    @property
    def disclosure_permitted(self) -> bool:
        return self.owner_approved_for_disclosure


def build_recognition_summary(case: RecognitionCase) -> dict[str, object]:
    """Return a neutral, evidence-labelled summary for owner review.

    This function does not infer a pay rise, promotion, legal entitlement,
    employee performance rating, or employer obligation.
    """
    return {
        "role_title": case.role_title,
        "official_expectation_count": len(case.official_expectations),
        "actual_work_count": len(case.actual_work),
        "potential_scope_gap_count": len(case.scope_gap_entries),
        "evidence_backed_count": len(case.evidence_backed_entries),
        "self_reported_or_unverified_count": sum(
            entry.evidence_status in {EvidenceStatus.SELF_REPORTED, EvidenceStatus.NOT_VERIFIED}
            for entry in case.actual_work
        ),
        "disputed_count": sum(entry.evidence_status == EvidenceStatus.DISPUTED for entry in case.actual_work),
        "measured_outcome_count": len(case.measured_outcomes),
        "requested_topics": tuple(topic.value for topic in case.requested_topics),
        "disclosure_permitted": case.disclosure_permitted,
        "prepared_at": case.prepared_at.isoformat(),
        "limitations": (
            "A potential scope gap is a prompt for human review, not proof of a contractual change.",
            "Self-reported, documented, corroborated, disputed and unverified claims remain distinct.",
            "Measured outcomes require a stated baseline, observed value and unit; causation is not inferred.",
            "AI-assisted output is not attributed to the human as unaided work.",
            "This summary does not determine compensation, job level, legal entitlement or employment status.",
            "No disclosure is authorised unless the owner explicitly approves it.",
        ),
    }


def validate_disclosure(case: RecognitionCase, selected_entry_ids: Iterable[str]) -> tuple[WorkRealityEntry, ...]:
    """Return only owner-selected entries, and only after explicit disclosure approval."""
    if not case.owner_approved_for_disclosure:
        raise PermissionError("owner approval is required before disclosure")
    selected = set(selected_entry_ids)
    known = {entry.entry_id: entry for entry in case.actual_work}
    if not selected or not selected.issubset(known):
        raise ValueError("select one or more known work entries")
    return tuple(known[entry_id] for entry_id in sorted(selected))
