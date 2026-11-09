import unittest
from datetime import datetime, timezone, timedelta
from raheb_human.workforce.transition_support import (
    TransitionConcern, SupportPreference, TransitionCheckIn, SupportResource,
    SupportPlan, ChangeCommunicationRecord, build_support_summary,
)

NOW = datetime(2026, 11, 9, tzinfo=timezone.utc)

class TransitionSupportTests(unittest.TestCase):
    def test_checkin_reflects_owner_selected_concerns_without_grief_stage(self):
        checkin = TransitionCheckIn(
            "owner-1", NOW,
            (TransitionConcern.PROFESSIONAL_IDENTITY, TransitionConcern.CAREER_DIRECTION),
            "I am unsure how my experience transfers to the new role.",
            (SupportPreference.CAREER_PLANNING,),
        )
        summary = build_support_summary(checkin)
        self.assertTrue(summary["not_a_diagnosis"])
        self.assertNotIn("grief_stage", summary)
        self.assertEqual(summary["concerns"], ("PROFESSIONAL_IDENTITY", "CAREER_DIRECTION"))

    def test_private_by_default(self):
        checkin = TransitionCheckIn("owner-1", NOW, ())
        self.assertTrue(build_support_summary(checkin)["private_by_default"])

    def test_no_employer_sharing_without_explicit_approval(self):
        with self.assertRaises(ValueError):
            SupportPlan("owner-1", NOW, (), ("Offer a private check-in",), share_with_employer=True)

    def test_owner_can_approve_specific_employer_sharing(self):
        plan = SupportPlan("owner-1", NOW, (), ("Share selected transition-support request",),
                           owner_approved=True, share_with_employer=True)
        self.assertTrue(plan.share_with_employer)

    def test_resources_require_source_reference(self):
        with self.assertRaises(ValueError):
            SupportResource("r1", "Counselling", "human_support", "Talk to a professional", "")

    def test_change_communication_records_facts_unknowns_and_next_update(self):
        record = ChangeCommunicationRecord(
            "org-1", NOW, ("The workflow pilot starts in January.",),
            ("No role decisions have been made.",), NOW + timedelta(days=7), "People Director"
        )
        self.assertEqual(len(record.confirmed_facts), 1)
        self.assertEqual(len(record.unknowns), 1)

    def test_rejects_naive_timestamps(self):
        with self.assertRaises(ValueError):
            TransitionCheckIn("owner-1", datetime(2026, 11, 9), ())

if __name__ == "__main__":
    unittest.main()
