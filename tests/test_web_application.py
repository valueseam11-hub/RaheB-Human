import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from raheb_human.api import app as api

class WebApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        api.DB_PATH=Path(self.temp.name)/"test.sqlite3"
        api.AGREEMENT_PATH=Path(self.temp.name)/"missing-agreement.md"
        api.PRIVACY_PATH=Path(self.temp.name)/"missing-privacy.md"
        api.init_db()
        self.client=TestClient(api.app)

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def demo_session(self):
        response=self.client.post("/api/demo/session",json={})
        self.assertEqual(response.status_code,200,response.text)
        return response.json()

    def test_health_and_security_headers(self):
        response=self.client.get("/api/health")
        self.assertEqual(response.status_code,200)
        self.assertFalse(response.json()["external_actions_enabled"])
        self.assertEqual(response.headers["x-frame-options"],"DENY")

    def test_public_config_fails_closed(self):
        config=self.client.get("/api/public-config").json()
        self.assertFalse(config["account_creation_enabled"])
        self.assertFalse(config["personal_data_upload_enabled"])
        self.assertFalse(config["external_actions_enabled"])

    def test_registration_disabled_without_legal_documents(self):
        response=self.client.post("/api/auth/register",json={
            "email":"person@example.test","password":"long-enough-demo-password"
        })
        self.assertEqual(response.status_code,403)

    def test_private_routes_require_authentication(self):
        self.assertEqual(self.client.get("/api/representatives").status_code,401)
        self.assertEqual(self.client.get("/api/evidence").status_code,401)

    def test_password_hash_is_salted_and_verified(self):
        first=api.password_hash("a-strong-password")
        second=api.password_hash("a-strong-password")
        self.assertNotEqual(first,second)
        self.assertTrue(api.password_matches("a-strong-password",first))
        self.assertFalse(api.password_matches("wrong-password",first))

    def test_demo_workspace_persists_owner_scoped_workflow_and_evidence(self):
        self.demo_session()
        rep=self.client.post("/api/representatives",json={
            "label":"Synthetic Finance Twin","profession":"Financial Operations"
        })
        self.assertEqual(rep.status_code,201,rep.text)
        rep_id=rep.json()["id"]
        self.assertEqual(rep.json()["state"],"DRAFT")
        source=self.client.post("/api/knowledge",json={
            "representative_id":rep_id,"fixture_id":"month_end"
        })
        self.assertEqual(source.status_code,201,source.text)
        self.assertEqual(source.json()["state"],"PENDING_OWNER_REVIEW")
        approved=self.client.post("/api/knowledge/"+source.json()["id"]+"/approve",json={})
        self.assertEqual(approved.status_code,200,approved.text)
        self.assertEqual(approved.json()["state"],"APPROVED")
        task=self.client.post("/api/tasks",json={
            "representative_id":rep_id,"task_type":"reconciliation_checklist",
            "request_text":"Prepare a reconciliation checklist from the approved synthetic source."
        })
        self.assertEqual(task.status_code,201,task.text)
        self.assertFalse(task.json()["external_action_performed"])
        reviewed=self.client.post("/api/tasks/"+task.json()["id"]+"/review",json={
            "decision":"approve_draft","note":"Reviewed synthetic draft"
        })
        self.assertEqual(reviewed.status_code,200,reviewed.text)
        self.assertEqual(reviewed.json()["state"],"HUMAN_REVIEWED_DRAFT")
        evidence=self.client.get("/api/evidence")
        self.assertTrue(evidence.json()["integrity_valid"])
        self.assertGreaterEqual(len(evidence.json()["records"]),4)

    def test_cross_site_state_change_is_rejected(self):
        response=self.client.post("/api/demo/session",json={},headers={"sec-fetch-site":"cross-site"})
        self.assertEqual(response.status_code,403)

    def test_demo_session_deletion_removes_owner_data(self):
        self.demo_session()
        rep=self.client.post("/api/representatives",json={
            "label":"Temporary Twin","profession":"Analyst"
        })
        self.assertEqual(rep.status_code,201)
        ended=self.client.delete("/api/demo/session")
        self.assertTrue(ended.json()["ended"])
        self.assertEqual(self.client.get("/api/representatives").status_code,401)

if __name__=="__main__":
    unittest.main()
