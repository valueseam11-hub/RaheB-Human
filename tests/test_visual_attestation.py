import unittest
from datetime import datetime, timezone
from raheb_human.core.visual_attestation import *

NOW=datetime(2026,11,9,10,0,tzinfo=timezone.utc)
class VisualAttestationTests(unittest.TestCase):
 def setUp(self):
  self.policy=AttestationPolicy()
  self.low=ModelAssessment("a1","vision","v1","sha256:"+"a"*64,.05,"calibrated-v1",RiskLevel.LOW)
 def test_critical_risk_routes_to_human_even_at_high_confidence(self):
  a=ModelAssessment("a2","vision","v1","sha256:"+"b"*64,.01,"cal-v1",RiskLevel.CRITICAL)
  self.assertEqual(route_for_attestation(a,self.policy,evidence_available=True).route,ReviewRoute.HUMAN_REVIEW)
 def test_missing_evidence_holds(self):
  self.assertEqual(route_for_attestation(self.low,self.policy,evidence_available=False).route,ReviewRoute.HOLD)
 def test_unknown_risk_routes_to_review(self):
  a=ModelAssessment("a3","m","v1","sha256:"+"c"*64,None,None,RiskLevel.UNKNOWN)
  self.assertEqual(route_for_attestation(a,self.policy,evidence_available=True).route,ReviewRoute.HUMAN_REVIEW)
 def test_capacity_exhaustion_holds(self):
  a=ModelAssessment("a4","m","v1","sha256:"+"d"*64,.8,"cal-v1",RiskLevel.LOW)
  self.assertEqual(route_for_attestation(a,self.policy,evidence_available=True,reviewer_capacity_available=False).route,ReviewRoute.HOLD)
 def test_original_evidence_required(self):
  e=VisualEvidence("e","s","a"*64,"image/jpeg",NOW,"cam","VERIFIED",False)
  with self.assertRaises(ValueError): e.validate()
 def test_independent_first_attestation(self):
  h=HumanAttestation("h","e","a","reviewer",HumanVerdict.UNCERTAIN,"partly occluded",NOW,"sha256:e","sha256:m",False)
  h.validate(self.policy)
 def test_model_first_rejected(self):
  h=HumanAttestation("h","e","a","reviewer",HumanVerdict.OBSERVED,"reviewed",NOW,"sha256:e","sha256:m",True)
  with self.assertRaises(ValueError): h.validate(self.policy)
 def test_unauthorised_intervention_rejected(self):
  i=Intervention("i","h","reviewer","hazard","SAFE_STOP",False,NOW)
  with self.assertRaises(PermissionError): validate_intervention(i)
 def test_human_correction_not_automatically_training_truth(self):
  f=CorrectionFeedback("f","h","vehicle","reviewer")
  with self.assertRaises(ValueError): validate_feedback_for_training(f)
 def test_validated_feedback_lineage(self):
  f=CorrectionFeedback("f","h","vehicle","reviewer",FeedbackStatus.ACCEPTED_FOR_EVALUATION)
  validate_feedback_for_training(f)

if __name__=="__main__": unittest.main()
