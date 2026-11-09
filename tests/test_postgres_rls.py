"""PostgreSQL RLS integration tests. Uses a disposable database only."""
import os
import unittest
from uuid import uuid4
try:
    import psycopg
except ImportError:
    psycopg = None
from raheb_human.storage.postgres import PostgresTenantStore

@unittest.skipUnless(os.getenv("RAHEB_TEST_DATABASE_URL") and psycopg,
                     "PostgreSQL integration service not configured")
class PostgresTenantIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn=os.environ["RAHEB_TEST_DATABASE_URL"]
        cls.store=PostgresTenantStore(cls.dsn)
        with psycopg.connect(cls.dsn,autocommit=True) as c:
            c.execute("CREATE ROLE raheb_app_test NOLOGIN")
            c.execute("GRANT USAGE ON SCHEMA public TO raheb_app_test")
            c.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO raheb_app_test")
            c.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO raheb_app_test")
    @classmethod
    def tearDownClass(cls):
        with psycopg.connect(cls.dsn,autocommit=True) as c:
            c.execute("DROP OWNED BY raheb_app_test")
            c.execute("DROP ROLE raheb_app_test")
    def test_rls_isolates_tenants_and_evidence_is_immutable(self):
        a,b=str(uuid4()),str(uuid4())
        ra,rb=str(uuid4()),str(uuid4())
        with psycopg.connect(self.dsn,autocommit=True) as c:
            c.execute("INSERT INTO raheb_owner_accounts(owner_id) VALUES (%s),(%s)",(a,b))
            c.execute("""INSERT INTO raheb_representatives
              (representative_id,owner_id,display_name,professional_role,version,state)
              VALUES (%s,%s,'Owner A','Analyst',1,'DRAFT'),(%s,%s,'Owner B','Analyst',1,'DRAFT')""",(ra,a,rb,b))
        with self.store.tenant_transaction(a) as c:
            c.execute("SET LOCAL ROLE raheb_app_test")
            rows=c.execute("SELECT representative_id FROM raheb_representatives").fetchall()
            self.assertEqual({str(row[0]) for row in rows},{ra})
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                c.execute("""INSERT INTO raheb_representatives
                  (representative_id,owner_id,display_name,professional_role,version,state)
                  VALUES (%s,%s,'Injected','Analyst',1,'DRAFT')""",(str(uuid4()),b))
        event=str(uuid4())
        with psycopg.connect(self.dsn,autocommit=True) as c:
            c.execute("""INSERT INTO raheb_evidence_events
              (event_id,owner_id,subject_type,subject_id,event_type,occurred_at,payload,previous_digest,record_digest)
              VALUES (%s,%s,'test','subject','TEST',now(),'{}'::jsonb,%s,%s)""",(event,a,b"0"*32,b"x"*32))
        with self.store.tenant_transaction(a) as c:
            c.execute("SET LOCAL ROLE raheb_app_test")
            with self.assertRaises(psycopg.errors.RaiseException):
                c.execute("DELETE FROM raheb_evidence_events WHERE event_id=%s",(event,))
