import unittest
from datetime import datetime, timezone, timedelta
from raheb_human.workforce.career_transition import (
    SkillEvidenceState, SkillRequirement, SkillEvidenceRecord,
    TransitionActionKind, DevelopmentAction, CareerTransitionPlan,
    HumanInteractionMode, HumanInteractionBoundary, build_transition_summary,
)

NOW = datetime(2026, 11, 9, tzinfo=timezone.utc)

def requirement(skill_id="ai-literacy"):
    return SkillRequirement(skill_id, "Evaluate AI-assisted outputs", "source://role-profile", NOW)

def plan(**overrides):
    values = dict(
        owner_id="owner-1", current_role="Operations Analyst",
        owner_defined_goal="Move into AI-enabled operations leadership",
        prepared_at=NOW, skill_requirements=(requirement(),),
        skill_evidence=(), development_actions=(
            DevelopmentAction("a1", "ai-literacy", TransitionActionKind.PRACTISE,
                              "Review and challenge AI-generated workflow reports"),
        ),
    )
    values.update(overrides)
    return CareerTransitionPlan(**values)

class CareerTransitionTests(unittest.TestCase):
    def test_absent_evidence_is_not_a_negative_skill_judgment(self):
        p = plan()
        self.assertEqual(p.evidence_state_for("ai-literacy"), SkillEvidenceState.NOT_YET_EVIDENCED)
        summary = build_transition_summary(p)
        self.assertTrue(any("Absence of evidence is not evidence" in x for x in summary["limitations"]))

    def test_demonstrated_skill_requires_attributable_evidence(self):
        record = SkillEvidenceRecord("ai-literacy", SkillEvidenceState.DEMONSTRATED,
                                     "portfolio://work-sample-1", "owner-1", NOW,
                                     "Human reviewed and corrected an AI workflow report")
        self.assertEqual(plan(skill_evidence=(record,)).evidence_state_for("ai-literacy"),
                         SkillEvidenceState.DEMONSTRATED)

    def test_disputed_evidence_is_not_silently_overwritten(self):
        records = (
            SkillEvidenceRecord("ai-literacy", SkillEvidenceState.DEMONSTRATED,
                                "portfolio://sample", "owner-1", NOW, "Work sample"),
            SkillEvidenceRecord("ai-literacy", SkillEvidenceState.DISPUTED,
                                "review://challenge", "reviewer-1", NOW, "Evidence challenged"),
        )
        self.assertEqual(plan(skill_evidence=records).evidence_state_for("ai-literacy"),
                         SkillEvidenceState.DISPUTED)

    def test_actions_must_map_to_goal_skill_requirements(self):
        with self.assertRaises(ValueError):
            plan(development_actions=(DevelopmentAction("x", "unknown", TransitionActionKind.LEARN, "Study"),))

    def test_practice_must_include_human_learner(self):
        with self.assertRaises(ValueError):
            DevelopmentAction("x", "ai-literacy", TransitionActionKind.PRACTISE,
                              "Practice task", human_practice_required=False)

    def test_ai_interaction_requires_scoped_expiring_approval(self):
        with self.assertRaises(ValueError):
            HumanInteractionBoundary("client relationship", HumanInteractionMode.AI_ASSISTED_WITH_APPROVAL,
                                     "owner-1", "Prepare client follow-up")
        boundary = HumanInteractionBoundary(
            "client relationship", HumanInteractionMode.AI_ASSISTED_WITH_APPROVAL,
            "owner-1", "Prepare a draft only", NOW, NOW + timedelta(hours=1)
        )
        self.assertEqual(boundary.mode, HumanInteractionMode.AI_ASSISTED_WITH_APPROVAL)

    def test_human_owned_communication_needs_no_ai_permission(self):
        boundary = HumanInteractionBoundary("client relationship", HumanInteractionMode.HUMAN_OWNED,
                                            "owner-1", "Owner chooses to conduct communication")
        self.assertEqual(boundary.mode, HumanInteractionMode.HUMAN_OWNED)

if __name__ == "__main__":
    unittest.main()
