import unittest
from datetime import datetime, timedelta, timezone

from raheb_human.core import (
    AuthorityContract, AuthorityDecision, CapabilityAssessment, CapabilityStatus,
    ConsentGrant, ConsentPurpose, EvidenceLedger, HumanCredential, TaskRequest,
    admit_action, consent_allows, evaluate_authority,
)
from raheb_human.core.capability import human_credential_implies_ai_capability


NOW = datetime(2030, 1, 1, tzinfo=timezone.utc)


def contract(**overrides):
    values = dict(
        contract_id="auth-1", owner_id="human-1", representative_id="rep-1",
        version=1, allowed_tasks=frozenset({"prepare_report"}),
        allowed_tools=frozenset({"document_reader"}),
        data_scopes=frozenset({"owner-approved:finance"}),
        expires_at=NOW + timedelta(days=1),
    )
    values.update(overrides)
    return AuthorityContract(**values)


class AuthorityTests(unittest.TestCase):
    def test_scoped_request_allowed(self):
        request = TaskRequest("prepare_report", "document_reader",
                              frozenset({"owner-approved:finance"}))
        self.assertEqual(evaluate_authority(contract(), request, now=NOW), AuthorityDecision.ALLOW)

    def test_missing_contract_holds_without_side_effect(self):
        result = admit_action(None, TaskRequest("anything", "any-tool"))
        self.assertEqual(result.decision, AuthorityDecision.HOLD)
        self.assertFalse(result.side_effect_permitted)

    def test_expired_or_revoked_contract_denied(self):
        request = TaskRequest("prepare_report", "document_reader")
        self.assertEqual(evaluate_authority(
            contract(expires_at=NOW), request, now=NOW), AuthorityDecision.DENY)
        self.assertEqual(evaluate_authority(
            contract(revoked=True), request, now=NOW), AuthorityDecision.DENY)

    def test_scope_escalation_denied(self):
        request = TaskRequest("prepare_report", "document_reader",
                              frozenset({"owner-approved:finance", "client:secret"}))
        self.assertEqual(evaluate_authority(contract(), request, now=NOW), AuthorityDecision.DENY)

    def test_high_impact_requires_human_approval(self):
        request = TaskRequest("prepare_report", "document_reader", high_impact=True)
        self.assertEqual(evaluate_authority(contract(), request, now=NOW), AuthorityDecision.HOLD)
        approved = TaskRequest("prepare_report", "document_reader",
                               high_impact=True, human_approval_present=True)
        self.assertEqual(evaluate_authority(contract(), approved, now=NOW), AuthorityDecision.ALLOW)


class ConsentTests(unittest.TestCase):
    def test_purposes_are_independent(self):
        grant = ConsentGrant("human-1", ConsentPurpose.SERVICE_PROCESSING, True,
                             "terms-v1", NOW)
        self.assertTrue(consent_allows((grant,), "human-1",
                                       ConsentPurpose.SERVICE_PROCESSING, now=NOW))
        self.assertFalse(consent_allows((grant,), "human-1",
                                        ConsentPurpose.MODEL_TRAINING, now=NOW))

    def test_latest_withdrawal_blocks(self):
        grants = (
            ConsentGrant("human-1", ConsentPurpose.PERSISTENT_MEMORY, True, "v1", NOW),
            ConsentGrant("human-1", ConsentPurpose.PERSISTENT_MEMORY, False, "v1",
                         NOW + timedelta(minutes=1)),
        )
        self.assertFalse(consent_allows(grants, "human-1",
                                        ConsentPurpose.PERSISTENT_MEMORY,
                                        now=NOW + timedelta(minutes=2)))


class EvidenceTests(unittest.TestCase):
    def test_chain_verifies_and_links(self):
        ledger = EvidenceLedger()
        first = ledger.append("TASK_RECEIVED", "rep-1", {"task": "draft"})
        second = ledger.append("HUMAN_APPROVED", "rep-1", {"approval": True})
        self.assertEqual(second.previous_digest, first.digest)
        self.assertTrue(ledger.verify())
        self.assertEqual(len(ledger.records), 2)


class CapabilityTests(unittest.TestCase):
    def test_human_credential_does_not_transfer(self):
        credential = HumanCredential("human-1", "accountancy", "issuer", "cred-1", True)
        self.assertFalse(human_credential_implies_ai_capability(credential))

    def test_capability_requires_matching_tested_scope(self):
        assessment = CapabilityAssessment("rep-1", "reconcile", "synthetic-ledger-v1",
                                          "assessment-1", CapabilityStatus.TESTED,
                                          "suite-1", "sha256:abc")
        self.assertTrue(assessment.supports("reconcile", "synthetic-ledger-v1"))
        self.assertFalse(assessment.supports("reconcile", "live-client-data"))


if __name__ == "__main__":
    unittest.main()
