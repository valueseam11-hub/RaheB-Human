import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "web" / "app.html"

class VisualAttestationPreviewPolishTests(unittest.TestCase):
    def test_workspace_uses_representative_language_and_exposes_visual_review(self):
        html = APP.read_text()
        self.assertIn("Your professional AI representative", html)
        self.assertNotIn("Your professional twin", html)
        self.assertIn('href="#visual-attestation"', html)

if __name__ == "__main__":
    unittest.main()
