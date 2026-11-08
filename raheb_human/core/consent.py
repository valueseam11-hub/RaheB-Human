"""Purpose-specific consent primitives; no purpose inherits another purpose."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class ConsentPurpose(StrEnum):
    SERVICE_PROCESSING = "service_processing"
    PERSISTENT_MEMORY = "persistent_memory"
    ANALYTICS = "analytics"
    MODEL_TRAINING = "model_training"
    EMPLOYER_SHARING = "employer_sharing"


@dataclass(frozen=True)
class ConsentGrant:
    subject_id: str
    purpose: ConsentPurpose
    granted: bool
    document_version: str
    recorded_at: datetime
    withdrawn_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.subject_id or not self.document_version:
            raise ValueError("subject_id and document_version are required")
        if self.recorded_at.tzinfo is None:
            raise ValueError("recorded_at must be timezone-aware")
        if self.withdrawn_at is not None and self.withdrawn_at.tzinfo is None:
            raise ValueError("withdrawn_at must be timezone-aware")


def consent_allows(
    grants: tuple[ConsentGrant, ...],
    subject_id: str,
    purpose: ConsentPurpose,
    *,
    now: datetime | None = None,
) -> bool:
    """Use the latest matching grant; withdrawal or denial means no consent."""
    instant = now or datetime.now(timezone.utc)
    matching = [
        grant for grant in grants
        if grant.subject_id == subject_id and grant.purpose == purpose
        and grant.recorded_at <= instant
    ]
    if not matching:
        return False
    latest = max(matching, key=lambda item: item.recorded_at)
    return latest.granted and (
        latest.withdrawn_at is None or latest.withdrawn_at > instant
    )
