import unittest
from datetime import datetime, timezone
from raheb_human.workforce.opportunity_intelligence import (
    SignalConfidence, LabourMarketSignal, OpportunityRequirement,
    CandidateEvidence, OpportunityAssessment, HiringProcessQuestions,
    ApplicationStage, ApplicationRecord, build_opportunity_summary,
)

NOW = datetime(2026, 11, 9, tzinfo=timezone.utc)

class OpportunityIntelligenceTests(unittest.TestCase):
    def test_market_signal_keeps_source_scope_and_projection_label(self):
        signal = LabourMarketSignal("s1", "Demand for AI literacy is increasing",
            "https://example.org/report", NOW, "Global", "Operations",
            SignalConfidence.REPORTED, "PROJECTED")
        self.assertEqual(signal.observed_or_projected, "PROJECTED")

    def test_market_signal_rejects_undated_or_unlabelled_claims(self):
        with self.assertRaises(ValueError):
            LabourMarketSignal("s1", "Claim", "source", datetime(2026, 1, 1),
                               "Global", "Sector", SignalConfidence.REPORTED, "OBSERVED")
        with self.assertRaises(ValueError):
            LabourMarketSignal("s2", "Claim", "source", NOW, "Global", "Sector",
                               SignalConfidence.REPORTED, "CERTAIN")

    def test_requirements_are_mapped_to_evidence_without_scoring_candidate(self):
        requirements = (
            OpportunityRequirement("r1", "Manage client relationships", "TASK",
                                   "Build and maintain client relationships", True),
            OpportunityRequirement("r2", "Use AI-assisted analysis", "SKILL",
                                   "Use AI tools to analyse operational data"),
        )
        evidence = (CandidateEvidence("r1", "portfolio://case-1", "owner-1",
                                      "Managed a client escalation", "Resolved within SLA", True),)
        assessment = OpportunityAssessment("o1", "Example Ltd", "Operations Lead",
            "https://example.org/job", NOW, requirements, evidence, "Interested in the role")
        summary = build_opportunity_summary(assessment)
        self.assertEqual(summary["requirements_without_evidence"], ["r2"])
        self.assertEqual(summary["requirements"][0]["evidence_status"], "EVIDENCE_PROVIDED")
        self.assertIn("Not-yet-evidenced does not mean", summary["limitations"][1])

    def test_unmapped_or_duplicate_evidence_is_rejected(self):
        req = OpportunityRequirement("r1", "Analyse data", "SKILL", "Analyse data")
        with self.assertRaises(ValueError):
            OpportunityAssessment("o", "Employer", "Analyst", "source", NOW, (req, req), (), "goal")
        with self.assertRaises(ValueError):
            OpportunityAssessment("o", "Employer", "Analyst", "source", NOW, (req,),
                (CandidateEvidence("r2", "ref", "owner", "context", "outcome"),), "goal")

    def test_hiring_process_prompts_surface_ai_policy_ambiguity(self):
        questions = HiringProcessQuestions("AI allowed for take-home only?",
            "Live interview and work sample", False, "Retention policy not explained",
            "Ask recruiter about accommodations")
        self.assertFalse(questions.human_review_available)

    def test_submission_requires_owner_action(self):
        with self.assertRaises(ValueError):
            ApplicationRecord("a1", "o1", ApplicationStage.SUBMITTED, NOW, True, False)
        record = ApplicationRecord("a1", "o1", ApplicationStage.SUBMITTED, NOW, True, True)
        self.assertTrue(record.submitted_by_owner)

if __name__ == "__main__":
    unittest.main()
