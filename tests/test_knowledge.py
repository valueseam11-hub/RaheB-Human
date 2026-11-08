import unittest
from datetime import datetime, timedelta, timezone

from raheb_human.core.consent import ConsentGrant, ConsentPurpose
from raheb_human.core.knowledge import (
    KnowledgeSource, KnowledgeState, PersonalKnowledgeStore,
)

NOW = datetime(2030, 1, 1, tzinfo=timezone.utc)


def grants(owner_id="owner-a", *, memory=True, service=True):
    items = []
    if service:
        items.append(ConsentGrant(
            owner_id, ConsentPurpose.SERVICE_PROCESSING, True, "service-v1", NOW
        ))
    if memory:
        items.append(ConsentGrant(
            owner_id, ConsentPurpose.PERSISTENT_MEMORY, True, "memory-v1", NOW
        ))
    return tuple(items)


def source(ref="source:ledger"):
    return KnowledgeSource(ref, "owner_document", "Finance procedure", "Owner upload")


class PersonalKnowledgeStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = PersonalKnowledgeStore()
        self.record = self.store.submit(
            "owner-a", "doc-1", source(),
            "Month-end reconciliation requires matching ledger entries to approved invoices.",
            "owner:finance", grants(), now=NOW,
        )

    def test_submission_requires_separate_persistent_memory_consent(self):
        with self.assertRaises(PermissionError):
            self.store.submit(
                "owner-a", "doc-no-memory", source("source:other"),
                "Approved operating procedure", "owner:finance",
                grants(memory=False), now=NOW,
            )

    def test_submission_is_pending_until_owner_approval(self):
        self.assertEqual(self.record.state, KnowledgeState.PENDING_REVIEW)
        self.assertEqual(self.store.retrieve(
            "owner-a", "reconciliation", frozenset({"owner:finance"}),
            grants(), now=NOW,
        ), ())
        approved = self.store.approve("owner-a", "doc-1", now=NOW)
        self.assertEqual(approved.state, KnowledgeState.APPROVED)
        self.assertEqual(approved.approved_by, "owner-a")

    def test_retrieval_is_owner_and_scope_isolated(self):
        self.store.approve("owner-a", "doc-1", now=NOW)
        own = self.store.retrieve(
            "owner-a", "reconciliation invoices", frozenset({"owner:finance"}),
            grants(), now=NOW,
        )
        foreign = self.store.retrieve(
            "owner-b", "reconciliation invoices", frozenset({"owner:finance"}),
            grants("owner-b"), now=NOW,
        )
        wrong_scope = self.store.retrieve(
            "owner-a", "reconciliation", frozenset({"employer:restricted"}),
            grants(), now=NOW,
        )
        self.assertEqual(len(own), 1)
        self.assertEqual(foreign, ())
        self.assertEqual(wrong_scope, ())
        self.assertEqual(own[0].source_ref, "source:ledger")
        self.assertEqual(own[0].content_digest, self.record.content_digest)

    def test_withdrawn_knowledge_disappears_from_retrieval(self):
        self.store.approve("owner-a", "doc-1", now=NOW)
        self.store.withdraw("owner-a", "doc-1", now=NOW)
        self.assertEqual(self.store.retrieve(
            "owner-a", "reconciliation", frozenset({"owner:finance"}),
            grants(), now=NOW,
        ), ())

    def test_withdrawn_consent_blocks_retrieval(self):
        self.store.approve("owner-a", "doc-1", now=NOW)
        withdrawn_memory = grants() + (ConsentGrant(
            "owner-a", ConsentPurpose.PERSISTENT_MEMORY, False, "memory-v2",
            NOW + timedelta(minutes=1),
        ),)
        with self.assertRaises(PermissionError):
            self.store.retrieve(
                "owner-a", "reconciliation", frozenset({"owner:finance"}),
                withdrawn_memory, now=NOW + timedelta(minutes=2),
            )

    def test_new_source_version_is_separate_and_pending(self):
        self.store.approve("owner-a", "doc-1", now=NOW)
        second = self.store.submit(
            "owner-a", "doc-2", source(),
            "Updated month-end reconciliation procedure uses two-person review.",
            "owner:finance", grants(), now=NOW + timedelta(days=1),
        )
        self.assertEqual(second.source_version, 2)
        self.assertEqual(second.state, KnowledgeState.PENDING_REVIEW)
        self.assertEqual(self.store.get("owner-a", "doc-1").state, KnowledgeState.APPROVED)

    def test_cross_owner_access_is_rejected(self):
        with self.assertRaises(PermissionError):
            self.store.approve("owner-b", "doc-1", now=NOW)
        self.assertIsNone(self.store.get("owner-b", "doc-1"))

    def test_content_size_limit_and_empty_content(self):
        with self.assertRaises(ValueError):
            self.store.submit(
                "owner-a", "empty", source("empty"), "  ",
                "owner:finance", grants(), now=NOW,
            )
        with self.assertRaises(ValueError):
            self.store.submit(
                "owner-a", "large", source("large"), "x" * 1_000_001,
                "owner:finance", grants(), now=NOW,
            )


if __name__ == "__main__":
    unittest.main()
