import tempfile,unittest
from pathlib import Path
from fastapi.testclient import TestClient
from raheb_human.api import app as api

class WebApplicationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  api.DB_PATH=Path(self.temp.name)/"test.sqlite3"
  api.AGREEMENT_PATH=Path(self.temp.name)/"missing-agreement.md"
  api.PRIVACY_PATH=Path(self.temp.name)/"missing-privacy.md"
  api.init_db();self.client=TestClient(api.app)
 def tearDown(self):
  self.client.close();self.temp.cleanup()
 def test_health_discloses_no_external_actions(self):
  r=self.client.get("/api/health");self.assertEqual(r.status_code,200);self.assertFalse(r.json()["external_actions_enabled"])
 def test_public_config_fails_closed(self):
  c=self.client.get("/api/public-config").json();self.assertFalse(c["account_creation_enabled"]);self.assertFalse(c["personal_data_upload_enabled"])
 def test_registration_disabled_without_legal_docs(self):
  r=self.client.post("/api/auth/register",json={"email":"person@example.test","password":"long-enough-demo-password"});self.assertEqual(r.status_code,403)
 def test_private_routes_require_authentication(self):
  self.assertEqual(self.client.get("/api/representatives").status_code,401);self.assertEqual(self.client.get("/api/evidence").status_code,401)
 def test_password_hash_salted_and_verified(self):
  a=api.password_hash("a-strong-password");b=api.password_hash("a-strong-password");self.assertNotEqual(a,b);self.assertTrue(api.password_matches("a-strong-password",a));self.assertFalse(api.password_matches("wrong-password",a))
 def test_audit_chain_detects_tampering(self):
  with api.db() as con:
   api.audit(con,"owner-1","TEST_EVENT","subject-1",{"value":"original"});self.assertTrue(api.verify_evidence(con,"owner-1"))
   con.execute("UPDATE evidence SET payload_json=? WHERE owner_id=?",('{"value":"changed"}',"owner-1"));self.assertFalse(api.verify_evidence(con,"owner-1"))
if __name__=="__main__":unittest.main()
