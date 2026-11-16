"""PostgreSQL tenant isolation integration tests; disposable DB only."""
import os
import unittest
from uuid import uuid4
import psycopg
from raheb_human.storage.postgres import PostgresTenantStore

DSN=os.getenv("RAHEB_TEST_DATABASE_URL")

@unittest.skipUnless(DSN,"RAHEB_TEST_DATABASE_URL not configured")
class TenantIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store=PostgresTenantStore(DSN)
        cls.role="raheb_ci_"+uuid4().hex[:12]
        with psycopg.connect(DSN,autocommit=True) as c:
            c.execute(f'CREATE ROLE "{cls.role}" NOLOGIN')
            c.execute(f'GRANT "{cls.role}" TO CURRENT_USER')
            c.execute(f'GRANT USAGE ON SCHEMA public TO "{cls.role}"')
            c.execute(f'GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO "{cls.role}"')
            c.execute(f'GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO "{cls.role}"')

    @classmethod
    def tearDownClass(cls):
        with psycopg.connect(DSN,autocommit=True) as c:
            c.execute(f'DROP OWNED BY "{cls.role}"')
            c.execute(f'DROP ROLE "{cls.role}"')

    def test_rls_hides_other_owner_and_rejects_cross_tenant_write(self):
        owner_a,owner_b=str(uuid4()),str(uuid4())
        rep_a,rep_b=str(uuid4()),str(uuid4())
        with psycopg.connect(DSN,autocommit=True) as c:
            c.execute("INSERT INTO raheb_owner_accounts(owner_id) VALUES (%s),(%s)",(owner_a,owner_b))
            c.execute("""INSERT INTO raheb_representatives
              (representative_id,owner_id,display_name,professional_role,version,state)
              VALUES (%s,%s,'Owner A','Analyst',1,'DRAFT'),(%s,%s,'Owner B','Analyst',1,'DRAFT')""",
              (rep_a,owner_a,rep_b,owner_b))
        with self.store.tenant_transaction(owner_a) as c:
            c.execute(f'SET LOCAL ROLE "{self.role}"')
            rows=c.execute("SELECT representative_id FROM raheb_representatives").fetchall()
            self.assertEqual({str(x["representative_id"]) for x in rows},{rep_a})
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                c.execute("""INSERT INTO raheb_representatives
                  (representative_id,owner_id,display_name,professional_role,version,state)
                  VALUES (%s,%s,'Injected','Analyst',1,'DRAFT')""",(str(uuid4()),owner_b))

    def test_evidence_events_cannot_be_updated_or_deleted(self):
        owner=str(uuid4())
        event=str(uuid4())
        with psycopg.connect(DSN,autocommit=True) as c:
            c.execute("INSERT INTO raheb_owner_accounts(owner_id) VALUES (%s)",(owner,))
            c.execute("""INSERT INTO raheb_evidence_events
              (event_id,owner_id,subject_type,subject_id,event_type,occurred_at,payload,previous_digest,record_digest)
              VALUES (%s,%s,'test','subject','TEST',now(),'{}'::jsonb,%s,%s)""",
              (event,owner,b"0"*32,b"x"*32))
        with self.store.tenant_transaction(owner) as c:
            c.execute(f'SET LOCAL ROLE "{self.role}"')
            with self.assertRaises(psycopg.errors.RaiseException):
                c.execute("DELETE FROM raheb_evidence_events WHERE event_id=%s",(event,))

if __name__=="__main__":
    unittest.main()
