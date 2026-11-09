import unittest
from datetime import datetime, timedelta, timezone
from raheb_human.workforce import *
NOW=datetime(2030,1,1,tzinfo=timezone.utc)
def task(**kw):
 v=dict(task_id="t1",title="Check completeness of ledger records",description="Check completeness using approved procedure",profession="accountant",data_scopes=frozenset({"employer:finance"}),known_procedure=True,human_owner_id="employee-1",employer_id="org-1"); v.update(kw); return TaskInput(**v)
class WorkforceTests(unittest.TestCase):
 def test_routine_is_supervised(self):
  a=assess_task(task()); self.assertEqual(a.category,TaskCategory.ROUTINE); self.assertEqual(a.delegation,DelegationMode.SUPERVISED_EXECUTION); self.assertFalse(a.can_run_without_human_review)
 def test_high_impact_is_human_owned(self):
  a=assess_task(task(title="Release payment",description="Transfer funds")); self.assertEqual(a.risk,RiskLevel.CRITICAL); self.assertEqual(a.delegation,DelegationMode.HUMAN_OWNED)
 def test_unknown_or_unscoped_holds(self):
  self.assertEqual(assess_task(task(title="Unusual request",description="Handle unusual case")).delegation,DelegationMode.HOLD); self.assertEqual(assess_task(task(data_scopes=frozenset())).delegation,DelegationMode.HOLD)
 def test_judgment_prepare_only(self):
  a=assess_task(task(title="Investigate variance",description="Investigate and resolve variance")); self.assertEqual(a.delegation,DelegationMode.PREPARE_ONLY)
 def test_draft_requires_evidence_and_scope(self):
  t=task(title="Research report",description="Research and summarise data"); w=HumanAIWorkbench(); ref=EvidenceReference("s","sha256:x","v1","employer:finance")
  d=w.prepare(t,assess_task(t),title="Brief",content="Draft",evidence=(ref,),now=NOW); self.assertTrue(d.draft_digest)
  with self.assertRaises(PermissionError): w.prepare(t,assess_task(t),title="Brief",content="Draft",evidence=(),now=NOW)
  with self.assertRaises(PermissionError): w.prepare(t,assess_task(t),title="Brief",content="Draft",evidence=(EvidenceReference("s","d","v","client:other"),),now=NOW)
 def test_human_owned_cannot_be_prepared(self):
  t=task(title="Sign contract",description="Sign contract",involves_external_commitment=True)
  with self.assertRaises(PermissionError): HumanAIWorkbench().prepare(t,assess_task(t),title="x",content="y",evidence=(EvidenceReference("s","d","v","employer:finance"),),now=NOW)
 def test_approval_is_bound_and_expires(self):
  b=create_approval_binding(task_id="t",task_digest="td",draft_digest="dd",owner_id="o",reviewer_id="o",representative_version="r1",authority_version="a1",expires_at=NOW+timedelta(minutes=5),nonce="once")
  args=dict(task_id="t",task_digest="td",draft_digest="dd",owner_id="o",reviewer_id="o",representative_version="r1",authority_version="a1",now=NOW)
  self.assertTrue(verify_approval_binding(b,**args)); self.assertFalse(verify_approval_binding(b,**{**args,"task_digest":"substituted"})); self.assertFalse(verify_approval_binding(b,**{**args,"now":NOW+timedelta(minutes=6)})); self.assertFalse(verify_approval_binding(b,**{**args,"consumed_nonces":("once",)}))
 def test_net_time_saved_includes_review_and_rework(self):
  self.assertEqual(calculate_net_time_saved(baseline_minutes=60,ai_assisted_minutes=20,human_review_minutes=15,rework_minutes=5),20); self.assertEqual(calculate_net_time_saved(baseline_minutes=30,ai_assisted_minutes=20,human_review_minutes=15,rework_minutes=5),-10)
 def test_employee_employer_boundary(self):
  b=WorkforceBoundary("e","org","rep",frozenset({"employer:finance"}),frozenset({"employee:personal"})); self.assertTrue(b.allows_employer_access("employer:finance")); self.assertFalse(b.allows_employer_access("employee:personal")); self.assertFalse(b.allows_employer_view_of_personal_data())
if __name__=="__main__": unittest.main()
