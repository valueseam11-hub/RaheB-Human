import unittest
from datetime import datetime, timedelta, timezone

from raheb_human.core.authority import AuthorityContract, AuthorityDecision, TaskRequest
from raheb_human.core.capability import CapabilityAssessment, CapabilityStatus
from raheb_human.core.consent import ConsentGrant, ConsentPurpose
from raheb_human.core.control_plane import (
    OwnerIdentity, RepresentativeControlPlane, RepresentativeSpec, RepresentativeState,
)

NOW = datetime(2030, 1, 1, tzinfo=timezone.utc)


def fixture():
    owner = OwnerIdentity("owner-1", True)
    spec = RepresentativeSpec("Alex", "Finance Operations", ("knowledge:approved:1",))
    consent = (ConsentGrant("owner-1", ConsentPurpose.SERVICE_PROCESSING, True, "terms-v1", NOW),)
    contract = AuthorityContract(
        "contract-1", "owner-1", "rep-1", 1,
        frozenset({"prepare_report", "approve_payment"}),
        frozenset({"document_reader", "payment_gateway"}),
        frozenset({"owner-approved:finance"}), NOW + timedelta(days=2),
    )
    capability = CapabilityAssessment(
        "rep-1", "prepare_report", "synthetic-finance-data",
        "assessment-1", CapabilityStatus.TESTED, "suite-v1", "sha256:evidence",
    )
    return owner, spec, consent, contract, capability


class ControlPlaneLifecycleTests(unittest.TestCase):
    def test_verified_owner_and_ai_disclosure_required(self):
        _, spec, _, _, _ = fixture()
        plane = RepresentativeControlPlane()
        with self.assertRaises(PermissionError):
            plane.register(OwnerIdentity("owner-1", False), "rep-1", spec)
        with self.assertRaises(ValueError):
            RepresentativeSpec("Alex", "Accountant", ("ref-1",), ai_disclosure_enabled=False)

    def test_activation_requires_service_consent(self):
        owner, spec, _, contract, _ = fixture()
        plane = RepresentativeControlPlane()
        plane.register(owner, "rep-1", spec)
        with self.assertRaises(PermissionError):
            plane.activate(owner.owner_id, "rep-1", contract, (), now=NOW)

    def test_activate_pause_revoke(self):
        owner, spec, consent, contract, _ = fixture()
        plane = RepresentativeControlPlane()
        plane.register(owner, "rep-1", spec)
        active = plane.activate(owner.owner_id, "rep-1", contract, consent, now=NOW)
        self.assertEqual(active.state, RepresentativeState.ACTIVE)
        self.assertEqual(plane.pause(owner.owner_id, "rep-1").state, RepresentativeState.PAUSED)
        self.assertEqual(plane.revoke(owner.owner_id, "rep-1").state, RepresentativeState.REVOKED)
        with self.assertRaises(PermissionError):
            plane.activate(owner.owner_id, "rep-1", contract, consent, now=NOW)

    def test_pause_cancels_pending_work(self):
        owner, spec, consent, contract, _ = fixture()
        plane = RepresentativeControlPlane()
        plane.register(owner, "rep-1", spec)
        plane.activate(owner.owner_id, "rep-1", contract, consent, now=NOW)
        plane.register_pending_task(owner.owner_id, "rep-1", "task-1")
        plane.pause(owner.owner_id, "rep-1")
        self.assertTrue(plane.was_task_cancelled("task-1"))


class ControlPlaneAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.owner, self.spec, self.consent, self.contract, self.capability = fixture()
        self.plane = RepresentativeControlPlane()
        self.plane.register(self.owner, "rep-1", self.spec)
        self.active = self.plane.activate(
            self.owner.owner_id, "rep-1", self.contract, self.consent, now=NOW
        )
        self.request = TaskRequest(
            "prepare_report", "document_reader", frozenset({"owner-approved:finance"})
        )

    def test_requires_capability_consent_and_current_version(self):
        missing = self.plane.admit(
            "owner-1", "rep-1", self.request, self.contract, None, self.consent,
            required_capability="prepare_report", required_scope="synthetic-finance-data",
            expected_representative_version=self.active.version, now=NOW,
        )
        self.assertEqual(missing.decision, AuthorityDecision.HOLD)
        no_consent = self.plane.admit(
            "owner-1", "rep-1", self.request, self.contract, self.capability, (),
            required_capability="prepare_report", required_scope="synthetic-finance-data",
            expected_representative_version=self.active.version, now=NOW,
        )
        self.assertEqual(no_consent.decision, AuthorityDecision.HOLD)
        stale = self.plane.admit(
            "owner-1", "rep-1", self.request, self.contract, self.capability, self.consent,
            required_capability="prepare_report", required_scope="synthetic-finance-data",
            expected_representative_version=1, now=NOW,
        )
        self.assertEqual(stale.decision, AuthorityDecision.HOLD)

    def test_valid_task_admitted_but_not_executed(self):
        result = self.plane.admit(
            "owner-1", "rep-1", self.request, self.contract, self.capability, self.consent,
            required_capability="prepare_report", required_scope="synthetic-finance-data",
            expected_representative_version=self.active.version, now=NOW,
        )
        self.assertEqual(result.decision, AuthorityDecision.ALLOW)
        self.assertFalse(result.side_effect_permitted)
        self.assertIn("no side effect", result.reason)

    def test_high_impact_requires_bound_one_time_approval(self):
        request = TaskRequest(
            "approve_payment", "payment_gateway",
            frozenset({"owner-approved:finance"}), high_impact=True,
        )
        capability = CapabilityAssessment(
            "rep-1", "approve_payment", "synthetic-payment-simulation",
            "assessment-2", CapabilityStatus.TESTED, "suite-v1", "sha256:payment",
        )
        missing = self.plane.admit(
            "owner-1", "rep-1", request, self.contract, capability, self.consent,
            required_capability="approve_payment", required_scope="synthetic-payment-simulation",
            expected_representative_version=self.active.version, now=NOW,
        )
        self.assertEqual(missing.decision, AuthorityDecision.HOLD)
        approval = self.plane.approve_task(
            "owner-1", "rep-1", request, self.contract, now=NOW
        )
        admitted = self.plane.admit(
            "owner-1", "rep-1", request, self.contract, capability, self.consent,
            required_capability="approve_payment", required_scope="synthetic-payment-simulation",
            approval_id=approval.approval_id,
            expected_representative_version=self.active.version, now=NOW,
        )
        self.assertEqual(admitted.decision, AuthorityDecision.ALLOW)
        replay = self.plane.admit(
            "owner-1", "rep-1", request, self.contract, capability, self.consent,
            required_capability="approve_payment", required_scope="synthetic-payment-simulation",
            approval_id=approval.approval_id,
            expected_representative_version=self.active.version, now=NOW,
        )
        self.assertEqual(replay.decision, AuthorityDecision.HOLD)

    def test_pause_invalidates_approval_and_stops_admission(self):
        request = TaskRequest("approve_payment", "payment_gateway", high_impact=True)
        approval = self.plane.approve_task("owner-1", "rep-1", request, self.contract, now=NOW)
        self.plane.pause("owner-1", "rep-1")
        result = self.plane.admit(
            "owner-1", "rep-1", request, self.contract, self.capability, self.consent,
            required_capability="prepare_report", required_scope="synthetic-finance-data",
            approval_id=approval.approval_id,
            expected_representative_version=self.active.version, now=NOW,
        )
        self.assertEqual(result.decision, AuthorityDecision.DENY)


if __name__ == "__main__":
    unittest.main()
