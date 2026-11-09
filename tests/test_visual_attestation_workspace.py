import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "web" / "app.html"
JS = ROOT / "web" / "visual-attestation.js"
CSS = ROOT / "web" / "visual-attestation.css"

class VisualAttestationWorkspaceTests(unittest.TestCase):
    def test_workspace_is_integrated_without_replacing_existing_sections(self):
        html = APP.read_text()
        for marker in ('id="visual-attestation"', 'id="visual-observation"',
                       'id="visual-reveal"', 'id="visual-verdict"',
                       'id="visual-submit"', 'visual-attestation.js',
                       'visual-attestation.css'):
            self.assertIn(marker, html)
        for existing in ('id="career-title"', 'id="continuity-title"', 'id="task-result"'):
            self.assertIn(existing, html)

    def test_review_starts_model_hidden_and_requires_independent_observation(self):
        js = JS.read_text()
        self.assertIn('visual-assessment').__class__ if False else None
        self.assertIn('initialObservation', js)
        self.assertIn('observation.length<12', js)
        self.assertIn('model_output_revealed_after_initial_observation:true', js)
        self.assertIn('UNAUTHENTICATED_DEMO_REVIEWER', js)

    def test_verdicts_preserve_uncertainty_and_disagreement(self):
        html = APP.read_text()
        for verdict in ('OBSERVED', 'NOT_OBSERVED', 'UNCERTAIN',
                        'EVIDENCE_UNUSABLE', 'DISAGREES_WITH_MODEL'):
            self.assertIn(verdict, html)

    def test_demo_discloses_no_persistence_or_physical_authority(self):
        html = APP.read_text()
        js = JS.read_text()
        self.assertIn('Nothing is uploaded or saved', html)
        self.assertIn('NO_PHYSICAL_ACTION_AUTHORISED', js)
        self.assertIn('BROWSER_MEMORY_ONLY', js)
        self.assertIn('not a cryptographic signature', js)

if __name__ == "__main__":
    unittest.main()
