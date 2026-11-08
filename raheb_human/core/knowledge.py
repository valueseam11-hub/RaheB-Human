"""Owner-scoped, provenance-aware approved knowledge reference store.

This is an in-memory reference component. It stores plain text supplied by a caller;
it does not parse files, scan malware, perform OCR, call models or persist to disk.
All source content remains untrusted data, never policy or authority.
"""
from __future__ import annotations

import hashlib
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from .consent import ConsentGrant, ConsentPurpose, consent_allows
from .evidence import EvidenceLedger

MAX_CONTENT_BYTES = 1_000_000


class KnowledgeState(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    WITHDRAWN = "WITHDRAWN"


@dataclass(frozen=True)
class KnowledgeSource:
    source_ref: str
    source_type: str
    title: str
    issuer_or_origin: str

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (
            self.source_ref, self.source_type, self.title, self.issuer_or_origin
        )):
            raise ValueError("source reference, type, title and origin are required")


@dataclass(frozen=True)
class KnowledgeDocument:
    document_id: str
    owner_id: str
    source: KnowledgeSource
    source_version: int
    content: str
    content_digest: str
    data_scope: str
    state: KnowledgeState
    submitted_at: datetime
    approved_at: datetime | None = None
    approved_by: str | None = None


@dataclass(frozen=True)
class KnowledgeHit:
    document_id: str
    source_ref: str
    source_title: str
    source_origin: str
    source_version: int
    content_digest: str
    data_scope: str
    snippet: str
    matched_terms: tuple[str, ...]
    trust_note: str = "Owner-approved source; content remains untrusted input."


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(token for token in re.findall(r"[a-zA-Z0-9_]{2,}", value.casefold()))


class PersonalKnowledgeStore:
    """Thread-safe, in-memory knowledge registry with explicit owner approval."""

    def __init__(self, evidence: EvidenceLedger | None = None) -> None:
        self.evidence = evidence or EvidenceLedger()
        self._documents: dict[str, KnowledgeDocument] = {}
        self._source_versions: dict[tuple[str, str], int] = {}
        self._lock = threading.RLock()

    def submit(
        self,
        owner_id: str,
        document_id: str,
        source: KnowledgeSource,
        content: str,
        data_scope: str,
        consent_grants: tuple[ConsentGrant, ...],
        *,
        now: datetime | None = None,
    ) -> KnowledgeDocument:
        instant = now or datetime.now(timezone.utc)
        if instant.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        if not owner_id.strip() or not document_id.strip() or not data_scope.strip():
            raise ValueError("owner, document and data scope identifiers are required")
        if not content.strip():
            raise ValueError("empty knowledge content is not accepted")
        if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise ValueError("content exceeds the 1 MB reference implementation limit")
        self._require_consent(consent_grants, owner_id, instant, require_memory=True)
        digest = _sha256(content)
        key = (owner_id, source.source_ref)
        with self._lock:
            if document_id in self._documents:
                raise ValueError("document_id must be unique")
            version = self._source_versions.get(key, 0) + 1
            self._source_versions[key] = version
            record = KnowledgeDocument(
                document_id=document_id,
                owner_id=owner_id,
                source=source,
                source_version=version,
                content=content,
                content_digest=digest,
                data_scope=data_scope,
                state=KnowledgeState.PENDING_REVIEW,
                submitted_at=instant,
            )
            self._documents[document_id] = record
            self.evidence.append("KNOWLEDGE_SUBMITTED", document_id, {
                "owner_id": owner_id,
                "source_ref": source.source_ref,
                "source_type": source.source_type,
                "source_version": version,
                "content_digest": digest,
                "data_scope": data_scope,
                "state": KnowledgeState.PENDING_REVIEW.value,
            }, occurred_at=instant)
            return record

    def approve(
        self,
        owner_id: str,
        document_id: str,
        *,
        now: datetime | None = None,
    ) -> KnowledgeDocument:
        instant = now or datetime.now(timezone.utc)
        with self._lock:
            record = self._require_owner(owner_id, document_id)
            if record.state != KnowledgeState.PENDING_REVIEW:
                raise PermissionError("only pending knowledge can be approved")
            if _sha256(record.content) != record.content_digest:
                raise ValueError("content digest mismatch; source integrity check failed")
            approved = KnowledgeDocument(
                document_id=record.document_id,
                owner_id=record.owner_id,
                source=record.source,
                source_version=record.source_version,
                content=record.content,
                content_digest=record.content_digest,
                data_scope=record.data_scope,
                state=KnowledgeState.APPROVED,
                submitted_at=record.submitted_at,
                approved_at=instant,
                approved_by=owner_id,
            )
            self._documents[document_id] = approved
            self.evidence.append("KNOWLEDGE_OWNER_APPROVED", document_id, {
                "owner_id": owner_id,
                "source_ref": record.source.source_ref,
                "source_version": record.source_version,
                "content_digest": record.content_digest,
                "data_scope": record.data_scope,
            }, occurred_at=instant)
            return approved

    def withdraw(
        self,
        owner_id: str,
        document_id: str,
        *,
        now: datetime | None = None,
    ) -> KnowledgeDocument:
        instant = now or datetime.now(timezone.utc)
        with self._lock:
            record = self._require_owner(owner_id, document_id)
            if record.state == KnowledgeState.WITHDRAWN:
                return record
            withdrawn = KnowledgeDocument(
                document_id=record.document_id,
                owner_id=record.owner_id,
                source=record.source,
                source_version=record.source_version,
                content=record.content,
                content_digest=record.content_digest,
                data_scope=record.data_scope,
                state=KnowledgeState.WITHDRAWN,
                submitted_at=record.submitted_at,
                approved_at=record.approved_at,
                approved_by=record.approved_by,
            )
            self._documents[document_id] = withdrawn
            self.evidence.append("KNOWLEDGE_WITHDRAWN", document_id, {
                "owner_id": owner_id,
                "source_ref": record.source.source_ref,
                "source_version": record.source_version,
                "content_digest": record.content_digest,
            }, occurred_at=instant)
            return withdrawn

    def retrieve(
        self,
        owner_id: str,
        query: str,
        allowed_scopes: frozenset[str],
        consent_grants: tuple[ConsentGrant, ...],
        *,
        limit: int = 5,
        now: datetime | None = None,
    ) -> tuple[KnowledgeHit, ...]:
        instant = now or datetime.now(timezone.utc)
        if instant.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        if not owner_id.strip() or not query.strip():
            raise ValueError("owner_id and query are required")
        if limit < 1 or limit > 20:
            raise ValueError("limit must be between 1 and 20")
        self._require_consent(consent_grants, owner_id, instant, require_memory=True)
        terms = set(_tokens(query))
        if not terms:
            return ()
        with self._lock:
            candidates: list[tuple[int, str, KnowledgeDocument, tuple[str, ...]]] = []
            for record in self._documents.values():
                if (
                    record.owner_id != owner_id
                    or record.state != KnowledgeState.APPROVED
                    or record.data_scope not in allowed_scopes
                ):
                    continue
                if _sha256(record.content) != record.content_digest:
                    continue
                matched = tuple(sorted(terms.intersection(_tokens(record.content))))
                if matched:
                    candidates.append((len(matched), record.document_id, record, matched))
            candidates.sort(key=lambda item: (-item[0], item[1]))
            hits: list[KnowledgeHit] = []
            for _, _, record, matched in candidates[:limit]:
                snippet = self._snippet(record.content, matched[0])
                hits.append(KnowledgeHit(
                    document_id=record.document_id,
                    source_ref=record.source.source_ref,
                    source_title=record.source.title,
                    source_origin=record.source.issuer_or_origin,
                    source_version=record.source_version,
                    content_digest=record.content_digest,
                    data_scope=record.data_scope,
                    snippet=snippet,
                    matched_terms=matched,
                ))
            return tuple(hits)

    def get(self, owner_id: str, document_id: str) -> KnowledgeDocument | None:
        with self._lock:
            record = self._documents.get(document_id)
            if record is None or record.owner_id != owner_id:
                return None
            return record

    @staticmethod
    def _require_consent(
        grants: tuple[ConsentGrant, ...],
        owner_id: str,
        instant: datetime,
        *,
        require_memory: bool,
    ) -> None:
        if not consent_allows(
            grants, owner_id, ConsentPurpose.SERVICE_PROCESSING, now=instant
        ):
            raise PermissionError("current service-processing consent is required")
        if require_memory and not consent_allows(
            grants, owner_id, ConsentPurpose.PERSISTENT_MEMORY, now=instant
        ):
            raise PermissionError("separate persistent-memory consent is required")

    def _require_owner(self, owner_id: str, document_id: str) -> KnowledgeDocument:
        record = self._documents.get(document_id)
        if record is None or record.owner_id != owner_id:
            raise PermissionError("knowledge document does not belong to this owner")
        return record

    @staticmethod
    def _snippet(content: str, term: str, width: int = 180) -> str:
        position = content.casefold().find(term.casefold())
        if position < 0:
            return content[:width]
        start = max(0, position - width // 3)
        end = min(len(content), start + width)
        return content[start:end].strip()
