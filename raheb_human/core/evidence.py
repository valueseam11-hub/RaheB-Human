"""Minimal append-only, hash-linked evidence ledger.

This is tamper-evident only. It is not signed, durable, independently witnessed,
or a proof that recorded statements are true.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class EvidenceRecord:
    sequence: int
    event_type: str
    subject_id: str
    occurred_at: str
    payload: dict[str, Any]
    previous_digest: str
    digest: str


class EvidenceLedger:
    def __init__(self) -> None:
        self._records: list[EvidenceRecord] = []

    @property
    def records(self) -> tuple[EvidenceRecord, ...]:
        return tuple(self._records)

    def append(
        self,
        event_type: str,
        subject_id: str,
        payload: dict[str, Any],
        *,
        occurred_at: datetime | None = None,
    ) -> EvidenceRecord:
        if not event_type or not subject_id:
            raise ValueError("event_type and subject_id are required")
        instant = occurred_at or datetime.now(timezone.utc)
        if instant.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        previous = self._records[-1].digest if self._records else "GENESIS"
        body = {
            "sequence": len(self._records) + 1,
            "event_type": event_type,
            "subject_id": subject_id,
            "occurred_at": instant.isoformat(),
            "payload": payload,
            "previous_digest": previous,
        }
        encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        record = EvidenceRecord(**body, digest=digest)
        self._records.append(record)
        return record

    def verify(self) -> bool:
        previous = "GENESIS"
        for index, record in enumerate(self._records, start=1):
            if record.sequence != index or record.previous_digest != previous:
                return False
            body = {
                "sequence": record.sequence,
                "event_type": record.event_type,
                "subject_id": record.subject_id,
                "occurred_at": record.occurred_at,
                "payload": record.payload,
                "previous_digest": record.previous_digest,
            }
            encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            expected = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
            if record.digest != expected:
                return False
            previous = record.digest
        return True
