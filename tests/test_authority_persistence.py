import json
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from raheb_human.authority.persistence import (
    AuthorityHold, AuthorityStoreError, admit_once, approve_exact_action,
    init_authority_schema, issue_warrant, revoke_warrant, verify_authority_events,
)


class DurableAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:", isolation_level="DEFERRED")
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA foreign_keys=ON")
        self.con.executescript("""
        CREATE TABLE users(id TEXT PRIMARY KEY);
        CREATE TABLE representatives(id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id), version INTEGER NOT NULL);
        """)
        self.owner, self.rep = "demo-owner", "rep-1"
        self.con.execute("INSERT INTO users(id) VALUES(?)", (self.owner,))
        self.con.execute("INSERT INTO representatives(id,owner_id,version) VALUES(?,?,?)",
                         (self.rep, self.owner, 2))
        init_authority_schema(self.con)
        self.con.commit()
        self.warrant = issue_warrant(self.con, owner_id=self.owner, representative_id=self.rep,
            representative_version=2, authorizer_id=self.owner, authority_source="INDIVIDUAL_OWNER",
            purpose="prepare:monthly-report", actions=["prepare_report"], resources=["demo:workspace"],
            limits={"money":"20.00","tokens":5000,"retries":1,"agent_count":1,"duration_seconds":120},
            expires_at=datetime.now(timezone.utc)+timedelta(hours=1))
        self.con.commit()
        self.output_digest = "a" * 64

    def tearDown(self):
        self.con.close()

    def make_approval(self):
        return approve_exact_action(self.con, owner_id=self.owner, approved_by=self.owner,
            warrant_id=self.warrant["warrant_id"], action="prepare_report",
            resource="demo:workspace", purpose="prepare:monthly-report",
            output_digest=self.output_digest, task_id="task-1",
            expires_at=datetime.now(timezone.utc)+timedelta(minutes=5))

    def test_approval_is_bound_to_exact_output_and_consumed_once(self):
        approval = self.make_approval()
        self.con.commit()
        with self.assertRaises(AuthorityHold):
            admit_once(self.con, owner_id=self.owner, approval_id=approval["approval_id"],
                idempotency_key="nonce-1", action="prepare_report", resource="demo:workspace",
                purpose="prepare:monthly-report", output_digest="b"*64,
                estimated_money="1", estimated_tokens=100)
        self.con.rollback()
        result = admit_once(self.con, owner_id=self.owner, approval_id=approval["approval_id"],
            idempotency_key="nonce-1", action="prepare_report", resource="demo:workspace",
            purpose="prepare:monthly-report", output_digest=self.output_digest,
            estimated_money="1", estimated_tokens=100)
        self.assertFalse(result["side_effect_permitted"])
        self.con.commit()
        with self.assertRaises(AuthorityHold):
            admit_once(self.con, owner_id=self.owner, approval_id=approval["approval_id"],
                idempotency_key="nonce-2", action="prepare_report", resource="demo:workspace",
                purpose="prepare:monthly-report", output_digest=self.output_digest,
                estimated_money="1", estimated_tokens=100)
        self.con.rollback()

    def test_parent_revocation_holds_child_approval(self):
        child = issue_warrant(self.con, owner_id=self.owner, representative_id=self.rep,
            representative_version=2, authorizer_id=self.owner, authority_source="INDIVIDUAL_OWNER",
            purpose="prepare:monthly-report", actions=["prepare_report"], resources=["demo:workspace"],
            limits={"money":"5","tokens":1000,"retries":0,"agent_count":1,"duration_seconds":60},
            expires_at=datetime.now(timezone.utc)+timedelta(minutes=30),
            parent_warrant_id=self.warrant["warrant_id"])
        self.con.commit()
        approval = approve_exact_action(self.con, owner_id=self.owner, approved_by=self.owner,
            warrant_id=child["warrant_id"], action="prepare_report", resource="demo:workspace",
            purpose="prepare:monthly-report", output_digest=self.output_digest, task_id=None,
            expires_at=datetime.now(timezone.utc)+timedelta(minutes=3))
        self.con.commit()
        revoke_warrant(self.con, owner_id=self.owner, warrant_id=self.warrant["warrant_id"],
                       revoked_by=self.owner, reason="owner withdrew authority")
        self.con.commit()
        with self.assertRaises(AuthorityHold):
            admit_once(self.con, owner_id=self.owner, approval_id=approval["approval_id"],
                idempotency_key="nonce-3", action="prepare_report", resource="demo:workspace",
                purpose="prepare:monthly-report", output_digest=self.output_digest,
                estimated_money="1", estimated_tokens=1)
        self.con.rollback()

    def test_representative_version_change_holds(self):
        approval = self.make_approval()
        self.con.commit()
        self.con.execute("UPDATE representatives SET version=3 WHERE id=?", (self.rep,))
        self.con.commit()
        with self.assertRaises(AuthorityHold):
            admit_once(self.con, owner_id=self.owner, approval_id=approval["approval_id"],
                idempotency_key="nonce-4", action="prepare_report", resource="demo:workspace",
                purpose="prepare:monthly-report", output_digest=self.output_digest,
                estimated_money="1", estimated_tokens=1)
        self.con.rollback()

    def test_cumulative_budget_exhaustion_holds(self):
        approval = self.make_approval()
        self.con.commit()
        admit_once(self.con, owner_id=self.owner, approval_id=approval["approval_id"],
            idempotency_key="nonce-5", action="prepare_report", resource="demo:workspace",
            purpose="prepare:monthly-report", output_digest=self.output_digest,
            estimated_money="15", estimated_tokens=4000)
        self.con.commit()
        second = self.make_approval()
        self.con.commit()
        with self.assertRaises(AuthorityHold):
            admit_once(self.con, owner_id=self.owner, approval_id=second["approval_id"],
                idempotency_key="nonce-6", action="prepare_report", resource="demo:workspace",
                purpose="prepare:monthly-report", output_digest=self.output_digest,
                estimated_money="6", estimated_tokens=100)
        self.con.rollback()

    def test_authority_event_chain_verifies_and_is_append_only(self):
        self.assertTrue(verify_authority_events(self.con, self.owner))
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("UPDATE authority_events SET event_type='FORGED' WHERE sequence=1")

    def test_organisation_authority_fails_closed_until_identity_is_ready(self):
        with self.assertRaises(AuthorityHold):
            issue_warrant(self.con, owner_id=self.owner, representative_id=self.rep,
                representative_version=2, authorizer_id="org-admin", authority_source="ORGANISATION",
                purpose="prepare:monthly-report", actions=["prepare_report"], resources=["demo:workspace"],
                limits={"money":"1","tokens":1}, expires_at=datetime.now(timezone.utc)+timedelta(minutes=5))


if __name__ == "__main__":
    unittest.main()
