"""Non-clinical, owner-controlled support for AI-related work transitions.

This module is not a mental-health assessment, diagnosis, therapy or HR
surveillance instrument. It stores only what the person chooses to record.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TransitionConcern(str, Enum):
    PROFESSIONAL_IDENTITY = "PROFESSIONAL_IDENTITY"
    CAREER_DIRECTION = "CAREER_DIRECTION"
    FINANCIAL_UNCERTAINTY = "FINANCIAL_UNCERTAINTY"
    SKILL_CONFIDENCE = "SKILL_CONFIDENCE"
    WORKLOAD_AND_BURNOUT = "WORKLOAD_AND_BURNOUT"
    TEAM_AND_BELONGING = "TEAM_AND_BELONGING"
    TRUST_AND_TRANSPARENCY = "TRUST_AND_TRANSPARENCY"
    OTHER = "OTHER"


class SupportPreference(str, Enum):
    REFLECT_PRIVATELY = "REFLECT_PRIVATELY"
    EXPLORE_OPTIONS = "EXPLORE_OPTIONS"
    SKILL_DEVELOPMENT = "SKILL_DEVELOPMENT"
    CAREER_PLANNING = "CAREER_PLANNING"
    PREPARE_HUMAN_CONVERSATION = "PREPARE_HUMAN_CONVERSATION"
    CONNECT_TO_HUMAN_SUPPORT = "CONNECT_TO_HUMAN_SUPPORT"


@dataclass(frozen=True)
class TransitionCheckIn:
    owner_id: str
    recorded_at: datetime
    concerns: tuple[TransitionConcern, ...]
    owner_words: str = ""
    requested_support: tuple[SupportPreference, ...] = ()
    private_by_default: bool = True

    def __post_init__(self):
        if not self.owner_id.strip():
            raise ValueError("owner identity is required")
        if self.recorded_at.tzinfo is None:
            raise ValueError("check-in timestamp must be timezone-aware")
        if len(set(self.concerns)) != len(self.concerns):
            raise ValueError("duplicate concerns are not allowed")
        if len(set(self.requested_support)) != len(self.requested_support):
            raise ValueError("duplicate support preferences are not allowed")
        if len(self.owner_words) > 4000:
            raise ValueError("owner reflection exceeds the 4000-character limit")


@dataclass(frozen=True)
class SupportResource:
    resource_id: str
    title: str
    resource_type: str
    description: str
    source_reference: str
    human_provider: bool = False

    def __post_init__(self):
        if not all((self.resource_id.strip(), self.title.strip(), self.resource_type.strip(),
                    self.description.strip(), self.source_reference.strip())):
            raise ValueError("support resource fields and source reference are required")


@dataclass(frozen=True)
class SupportPlan:
    owner_id: str
    created_at: datetime
    selected_preferences: tuple[SupportPreference, ...]
    actions: tuple[str, ...]
    resources: tuple[SupportResource, ...] = ()
    owner_approved: bool = False
    share_with_employer: bool = False

    def __post_init__(self):
        if not self.owner_id.strip():
            raise ValueError("owner identity is required")
        if self.created_at.tzinfo is None:
            raise ValueError("plan timestamp must be timezone-aware")
        if any(not action.strip() for action in self.actions):
            raise ValueError("support actions cannot be blank")
        if self.share_with_employer and not self.owner_approved:
            raise ValueError("employer sharing requires explicit owner approval")
        if len(set(self.selected_preferences)) != len(self.selected_preferences):
            raise ValueError("duplicate support preferences are not allowed")


@dataclass(frozen=True)
class ChangeCommunicationRecord:
    organisation_id: str
    recorded_at: datetime
    confirmed_facts: tuple[str, ...]
    unknowns: tuple[str, ...]
    next_update_at: datetime | None
    accountable_contact: str

    def __post_init__(self):
        if not all((self.organisation_id.strip(), self.accountable_contact.strip())):
            raise ValueError("organisation and accountable contact are required")
        if self.recorded_at.tzinfo is None:
            raise ValueError("record timestamp must be timezone-aware")
        if self.next_update_at is not None:
            if self.next_update_at.tzinfo is None or self.next_update_at < self.recorded_at:
                raise ValueError("next update must be timezone-aware and not precede this record")
        if any(not item.strip() for item in self.confirmed_facts + self.unknowns):
            raise ValueError("facts and unknowns cannot be blank")


def build_support_summary(check_in: TransitionCheckIn) -> dict[str, object]:
    """Summarise the person's own selections without diagnosing or categorising them."""
    return {
        "owner_id": check_in.owner_id,
        "recorded_at": check_in.recorded_at.isoformat(),
        "concerns": tuple(item.value for item in check_in.concerns),
        "requested_support": tuple(item.value for item in check_in.requested_support),
        "owner_words": check_in.owner_words,
        "private_by_default": check_in.private_by_default,
        "not_a_diagnosis": True,
        "limitations": (
            "This is a self-directed reflection, not a clinical assessment or diagnosis.",
            "No grief stage, mental-health condition, resilience score or fitness-for-work score is inferred.",
            "The person chooses whether to share any information with an employer or another party.",
            "Where distress is significant or persistent, support from a qualified human professional may be appropriate.",
        ),
    }
