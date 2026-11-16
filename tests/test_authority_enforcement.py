import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from raheb_human.authority.engine import (
    ActionRequest, AuthorityEnforcement, AuthorityError, AuthorityWarrant,
    ConsequenceLimits, Decision, RevocationRegistry, delegate,
)


class AuthorityEnforcementTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.limits = ConsequenceLimits(money=Decimal("50"), tokens=10000,
                                        retries=2, agent_count=3, duration_seconds=300)
        self.warrant = AuthorityWarrant.issue(
            owner_id="owner-1", representative_id="rep-1", representative_version=4,
            authorizer_id="owner-1", authority_source="individual_owner",
            purpose="reconcile:period-2026-10",
            allowed_actions=frozenset({"prepare_report", "read_ledger"}),
            allowed_resources=frozenset({"workspace:finance-demo"}),
            expires_at=self.now + timedelta(hours=1), limits=self.limits,
            approval_required=True, issued_at=self.now - timedelta(minutes=1))
        self.registry = RevocationRegistry()
        self.engine = AuthorityEnforcement([self.warrant], self.registry)

    def request(self, **overrides):
        values = dict(owner_id="owner-1", representative_id="rep-1",
            representative_version=4, action="prepare_report",
            resource="workspace:finance-demo", purpose="reconcile:period-2026-10",
            idempotency_key="once-1", estimated_money=Decimal("2"),
            estimated_tokens=500, retry_number=0, active_agent_count=1,
            elapsed_seconds=10, human_approval_id="approval-1")
        values.update(overrides)
        return ActionRequest(**values)

    def test_exact_current_authority_permits(self):
        self.assertEqual(self.engine.admit(self.warrant.warrant_id,
            self.request(), self.now).decision, Decision.PERMIT)

    def test_missing_approval_holds(self):
        self.assertEqual(self.engine.admit(self.warrant.warrant_id,
            self.request(human_approval_id=None), self.now).decision, Decision.HOLD)

    def test_wrong_purpose_is_denied(self):
        self.assertEqual(self.engine.admit(self.warrant.warrant_id,
            self.request(purpose="send:marketing"), self.now).decision, Decision.DENY)

    def test_version_substitution_holds(self):
        self.assertEqual(self.engine.admit(self.warrant.warrant_id,
            self.request(representative_version=5), self.now).decision, Decision.HOLD)

    def test_revocation_holds(self):
        self.registry.revoke(self.warrant.warrant_id, "owner withdrew consent")
        self.assertEqual(self.engine.admit(self.warrant.warrant_id,
            self.request(), self.now).decision, Decision.HOLD)

    def test_child_cannot_expand_actions_or_resources(self):
        with self.assertRaises(AuthorityError):
            delegate(self.warrant, child_authorizer_id="agent-1",
                purpose=self.warrant.purpose, actions={"delete_ledger"},
                resources={"workspace:finance-demo"}, expires_at=self.warrant.expires_at,
                limits=self.limits)

    def test_child_expiry_cannot_outlive_parent(self):
        with self.assertRaises(AuthorityError):
            delegate(self.warrant, child_authorizer_id="agent-1",
                purpose=self.warrant.purpose, actions={"read_ledger"},
                resources={"workspace:finance-demo"},
                expires_at=self.warrant.expires_at + timedelta(seconds=1),
                limits=self.limits)

    def test_parent_revocation_propagates_to_child(self):
        child = delegate(self.warrant, child_authorizer_id="agent-1",
            purpose=self.warrant.purpose, actions={"read_ledger"},
            resources={"workspace:finance-demo"},
            expires_at=self.now + timedelta(minutes=20),
            limits=ConsequenceLimits(money=Decimal("10"), tokens=1000,
                retries=1, agent_count=1, duration_seconds=60))
        engine = AuthorityEnforcement([self.warrant, child], self.registry)
        self.registry.revoke(self.warrant.warrant_id, "withdrawn")
        result = engine.admit(child.warrant_id, self.request(), self.now)
        self.assertEqual(result.decision, Decision.HOLD)
        self.assertIn("revoked", result.reason)

    def test_budget_exhaustion_holds(self):
        first = self.engine.admit(self.warrant.warrant_id,
            self.request(estimated_money=Decimal("40"), estimated_tokens=8000), self.now)
        self.assertEqual(first.decision, Decision.PERMIT)
        second = self.engine.admit(self.warrant.warrant_id,
            self.request(idempotency_key="once-2", estimated_money=Decimal("20"),
                         estimated_tokens=1000), self.now)
        self.assertEqual(second.decision, Decision.HOLD)

    def test_idempotent_reservation_does_not_double_count(self):
        request = self.request()
        self.assertEqual(self.engine.admit(self.warrant.warrant_id,
            request, self.now).decision, Decision.PERMIT)
        self.assertEqual(self.engine.admit(self.warrant.warrant_id,
            request, self.now).decision, Decision.PERMIT)
        self.assertEqual(self.engine.budgets[self.warrant.warrant_id].totals(),
                         (Decimal("2"), 500))

    def test_missing_warrant_holds(self):
        self.assertEqual(self.engine.admit("unknown", self.request(),
            self.now).decision, Decision.HOLD)


if __name__ == "__main__":
    unittest.main()
