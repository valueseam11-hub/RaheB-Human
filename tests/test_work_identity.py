import unittest
from datetime import datetime, timezone
from raheb_human.workforce import (
    EvidenceStatus, RecognitionTopic, RoleExpectation, WorkRealityEntry,
    RecognitionCase, build_recognition_summary, validate_disclosure,
)

NOW = datetime(2026, 11, 9, tzinfo=timezone.utc)

def entry(**overrides):
    values = dict(
        entry_id="w1", description="Use AI-assisted reconciliation and resolve exceptions",
        first_observed_at=NOW, last_observed_at=NOW, frequency="weekly",
        evidence_status=EvidenceStatus.SELF_REPORTED, ai_assistance_used=True,
        human_responsibility="Verify source records and approve final reconciliation",
    )
    values.update(overrides)
    return WorkRealityEntry(**values)

def case(**overrides):
    values = dict(
        owner_id="employee-1", role_title="Finance Officer",
        official_expectations=(RoleExpectation("r1", "Prepare monthly reconciliation", "signed role profile", NOW),),
        actual_work=(entry(),),
        requested_topics=(RecognitionTopic.ROLE_SCOPE, RecognitionTopic.WORKLOAD),
        prepared_at=NOW,
    )
    values.update(overrides)
    return RecognitionCase(**values)

class WorkIdentityTests(unittest.TestCase):
    def test_scope_gap_is_only_a_review_prompt(self):
        c = case()
        self.assertEqual(len(c.scope_gap_entries), 1)
        summary = build_recognition_summary(c)
        self.assertEqual(summary["potential_scope_gap_count"], 1)
        self.assertTrue(any("not proof" in item for item in summary["limitations"]))

    def test_evidence_levels_are_not_collapsed(self):
        c = case(actual_work=(
            entry(entry_id="self"),
            entry(entry_id="doc", evidence_status=EvidenceStatus.DOCUMENTED, evidence_refs=("ticket://123",)),
            entry(entry_id="disputed", evidence_status=EvidenceStatus.DISPUTED),
        ))
        summary = build_recognition_summary(c)
        self.assertEqual(summary["evidence_backed_count"], 1)
        self.assertEqual(summary["self_reported_or_unverified_count"], 1)
        self.assertEqual(summary["disputed_count"], 1)

    def test_measured_outcome_requires_baseline_observed_and_unit(self):
        with self.assertRaises(ValueError):
            entry(baseline_value=10)
        measured = entry(baseline_value=120, observed_value=45, unit="minutes", outcome_metric="cycle time")
        self.assertEqual(measured.observed_value, 45)

    def test_documented_entry_requires_reference(self):
        with self.assertRaises(ValueError):
            entry(evidence_status=EvidenceStatus.DOCUMENTED)

    def test_no_disclosure_without_owner_approval(self):
        with self.assertRaises(PermissionError):
            validate_disclosure(case(), ("w1",))

    def test_disclosure_is_explicit_and_selected(self):
        c = case(owner_approved_for_disclosure=True)
        self.assertEqual(tuple(x.entry_id for x in validate_disclosure(c, ("w1",))), ("w1",))
        with self.assertRaises(ValueError):
            validate_disclosure(c, ("unknown",))

    def test_ai_assistance_and_human_responsibility_are_separate(self):
        item = entry()
        self.assertTrue(item.ai_assistance_used)
        self.assertIn("approve", item.human_responsibility)

    def test_role_expectation_requires_timezone(self):
        with self.assertRaises(ValueError):
            RoleExpectation("r", "Do work", "contract", datetime(2026, 1, 1))

if __name__ == "__main__":
    unittest.main()
